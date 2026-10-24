# Mainland China student-career sources and tool choices

Research checked on October 24, 2026. This is an implementation research record, not a claim that the app retrieved these pages during every conversation.

## Primary sources

| Source | Verified entry or supporting page | Appropriate use and access limit |
| --- | --- | --- |
| National College Student Employment Service Platform (NCSS/24365) | [Platform](https://www.ncss.cn/) and [Ministry of Education platform notice](https://www.moe.gov.cn/srcsite/A15/s3265/202204/t20220406_614117.html) | The ministry identifies NCSS as the national student employment platform. The notice describes student access using a CHSI account. It establishes provenance, not current vacancy availability. |
| NCSS graduate jobs | [Jobs entry](https://www.ncss.cn/student/jobs/index.html) and [indexed jobs portal](https://jobs.ncss.cn/) | Useful for navigating to employer listings. The direct jobs entry returned only dynamic input placeholders to the research fetcher. Read the actual posting in a browser and confirm its deadline. |
| NCSS internships | [Internship entry](https://www.ncss.cn/student/jobs/internindex.html) | The route was reachable but exposed only dynamic placeholders to the fetcher. An [NCSS institution portal](https://jqzy.ncss.cn/student/jobs/internindex.html) exposed internship filters in search results. A link is not a verified open position. |
| Ministry of Human Resources and Social Security | [Ministry](https://www.mohrss.gov.cn/) and [public employment portal](https://job.mohrss.gov.cn/) | Official discovery and policy context. Direct research fetches timed out; do not present that as a successful live retrieval. |
| National Bureau of Statistics | [What average wages measure](https://www.stats.gov.cn/zs/tjws/tjzb/202301/t20230101_1903795.html) | Explains statistical coverage and why an aggregate average is not an individual's wage. Use methodology and dated context; do not convert national averages into a graduate salary promise. |

Each institution is explicitly identified. A generic `.gov` or `.edu` suffix is insufficient to establish that a result belongs to this mainland China student-career workflow. A trusted publisher still does not establish the truth of every extracted sentence.

## What a market brief can claim

A useful brief separates source-backed observations, practical suggestions, and unanswered questions. A job-specific salary, hiring deadline, degree requirement, graduation-year rule, or internship schedule needs a relevant dated posting. Unknown or inaccessible fields stay unknown. Record whether a salary is monthly or annual, gross or net, and whether it is an employer-posted range or an aggregate statistic.

Internship availability, campus eligibility, and application deadlines can change. General ministry guidance does not prove eligibility for an individual employer. The applicant should check the employer's posting and application channel before acting.

## Search-first decision

The repository already uses Pydantic, Streamlit, a bounded search transport, source-reference checks, and a permission gateway. Those components provide the required foundation. The available connector and skill catalog was checked; no runtime connector was needed for a local, session-only tracker. Public PyPI, official Python documentation, and public GitHub pages were reviewed. npm was not relevant to this Python application. No authenticated GitHub code search was required or claimed.

| Candidate | Fit | Maintenance/license/dependency consideration | Decision |
| --- | --- | --- | --- |
| Existing [Pydantic](https://pypi.org/project/pydantic/) | Profile and application field validation | Already pinned in this project; documented Python validation library | Reuse the installed dependency. |
| Python [csv](https://docs.python.org/3/library/csv.html) and [re](https://docs.python.org/3/library/re.html) | Explicit CSV schema and deterministic keyword aliases | Standard library; no added runtime dependency | Use small domain-specific functions around these primitives. |
| [RapidFuzz](https://pypi.org/project/RapidFuzz/) | Fuzzy text similarity | MIT library with documented similarity scorers; its current Windows installation notes describe a runtime dependency | Do not add it for literal skill mentions. Similarity would not establish ability or job fit. |
| [csvkit](https://github.com/wireservice/csvkit) | Broad CSV conversion and command-line analysis | MIT project; broader tooling and inference behavior than this app needs | Do not add a CLI suite for a small in-memory table. |

The custom portion is the student-career schema and fixed skill aliases, not a new CSV parser, fuzzy-matching engine, or agent framework. No package installation or scrape of a third-party job board is required for the local tools.
