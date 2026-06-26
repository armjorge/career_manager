from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.auth import get_current_user_id
from backend.app.database import db_cursor, schema
from backend.app.schemas import AnalyticsMetrics, AnalyticsSummary, LabelCount, MonthlyActivity

router = APIRouter(tags=["analytics"])


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(user_id: UUID = Depends(get_current_user_id)) -> AnalyticsSummary:
    s = schema()
    uid = str(user_id)

    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT TO_CHAR(fa.created_at, 'YYYY-MM') AS year_month, COUNT(*) AS apps
            FROM {s}.fact_application fa
            WHERE fa.user_id = %s
            GROUP BY 1
            ORDER BY 1
            """,
            (uid,),
        )
        apps_by_month = {row["year_month"]: int(row["apps"]) for row in cur.fetchall()}

        cur.execute(
            f"""
            SELECT TO_CHAR(fa.created_at, 'YYYY-MM') AS year_month, COUNT(*) AS resumes
            FROM {s}.fact_application fa
            JOIN {s}.dim_resume_details drd
                ON drd.application_id = fa.application_id AND drd.user_id = fa.user_id
            JOIN {s}.dim_file df
                ON df.file_id = drd.file_id AND df.user_id = fa.user_id
            WHERE fa.user_id = %s
              AND df.file_hash IS NOT NULL
              AND df.active_status = TRUE
            GROUP BY 1
            ORDER BY 1
            """,
            (uid,),
        )
        resumes_by_month = {row["year_month"]: int(row["resumes"]) for row in cur.fetchall()}

        cur.execute(
            f"""
            SELECT TO_CHAR(fa.created_at, 'YYYY-MM') AS year_month, COUNT(*) AS cover_letters
            FROM {s}.fact_application fa
            JOIN {s}.dim_cover_letter dcl
                ON dcl.application_id = fa.application_id AND dcl.user_id = fa.user_id
            JOIN {s}.dim_file df
                ON df.file_id = dcl.file_id AND df.user_id = fa.user_id
            WHERE fa.user_id = %s
              AND df.file_hash IS NOT NULL
              AND df.active_status = TRUE
            GROUP BY 1
            ORDER BY 1
            """,
            (uid,),
        )
        cover_letters_by_month = {
            row["year_month"]: int(row["cover_letters"]) for row in cur.fetchall()
        }

        months = sorted(set(apps_by_month) | set(resumes_by_month) | set(cover_letters_by_month))
        monthly_activity = [
            MonthlyActivity(
                year_month=month,
                apps=apps_by_month.get(month, 0),
                resumes=resumes_by_month.get(month, 0),
                cover_letters=cover_letters_by_month.get(month, 0),
            )
            for month in months
        ]

        cur.execute(
            f"""
            SELECT status AS name, COUNT(*) AS count
            FROM {s}.fact_application
            WHERE user_id = %s
            GROUP BY 1
            ORDER BY 1
            """,
            (uid,),
        )
        status_distribution = [
            LabelCount(name=str(row["name"]), count=int(row["count"])) for row in cur.fetchall()
        ]

        cur.execute(
            f"""
            SELECT dl.language AS name, COUNT(*) AS count
            FROM {s}.fact_application fa
            JOIN {s}.dim_language dl
                ON dl.lang_id = fa.lang_id AND dl.user_id = fa.user_id
            WHERE fa.user_id = %s
            GROUP BY 1
            ORDER BY count DESC, name
            """,
            (uid,),
        )
        language_distribution = [
            LabelCount(name=str(row["name"]), count=int(row["count"])) for row in cur.fetchall()
        ]

        cur.execute(
            f"""
            SELECT COALESCE(djc.category_name, 'Uncategorized') AS name, COUNT(*) AS count
            FROM {s}.fact_application fa
            LEFT JOIN {s}.dim_job_category djc
                ON djc.job_cat_id = fa.job_cat_id AND djc.user_id = fa.user_id
            WHERE fa.user_id = %s
            GROUP BY 1
            ORDER BY count DESC, name
            """,
            (uid,),
        )
        category_distribution = [
            LabelCount(name=str(row["name"]), count=int(row["count"])) for row in cur.fetchall()
        ]

        cur.execute(
            f"""
            WITH industries AS (
                SELECT dc.company_id, dct.type_name
                FROM {s}.dim_company dc
                LEFT JOIN {s}.dim_ctype dct
                    ON dc.ctype_id = dct.ctype_id AND dct.user_id = dc.user_id
                WHERE dc.user_id = %s
            )
            SELECT COALESCE(ind.type_name, 'Other/Unknown') AS name, COUNT(*) AS count
            FROM {s}.fact_application fa
            LEFT JOIN industries ind ON fa.company_id = ind.company_id
            WHERE fa.user_id = %s
            GROUP BY 1
            ORDER BY count DESC, name
            """,
            (uid, uid),
        )
        industry_distribution = [
            LabelCount(name=str(row["name"]), count=int(row["count"])) for row in cur.fetchall()
        ]

    total_applications = sum(item.apps for item in monthly_activity)
    ready_resumes = sum(item.resumes for item in monthly_activity)
    ready_cover_letters = sum(item.cover_letters for item in monthly_activity)
    cv_prep_rate = (ready_resumes / total_applications * 100) if total_applications > 0 else 0.0

    return AnalyticsSummary(
        metrics=AnalyticsMetrics(
            total_applications=total_applications,
            ready_resumes=ready_resumes,
            ready_cover_letters=ready_cover_letters,
            cv_prep_rate=round(cv_prep_rate, 1),
        ),
        monthly_activity=monthly_activity,
        status_distribution=status_distribution,
        language_distribution=language_distribution,
        category_distribution=category_distribution,
        industry_distribution=industry_distribution,
    )
