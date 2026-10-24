# Student career guide

The Graduate Career Workbench is for students and recent graduates exploring mainland China internships and campus recruitment. The interface and generated guidance use English. Job descriptions may be in Chinese or English.

Choose **Career chat**, **Market brief**, or **Job tools** at the top of the page. You can use the local profile, keyword comparison, and tracker without configuring DeepSeek.

## 1. Save a useful profile

Open **Your student profile** in the sidebar. Choose your study stage, target role, target city, job-search goal, skills you have practised, and preparation hours per week. You can also enter a major or field of study. Select **Save profile** to apply the changes.

The choices include an exploring option and any mainland China city. Weekly preparation time is 1–40 hours. The app treats selected skills as self-reported, not independently verified.

Saving changed details starts a fresh conversation and clears the previous market brief and skill comparison so they do not silently retain an old target. Application records remain separate. Editing a field without saving does not update the active profile.

For example: a final-year economics student targeting data analysis in Shanghai might select Excel and communication, an internship goal, and five preparation hours per week. Describe any real projects, graduation-year restrictions, start date, or schedule constraints in chat when relevant. Do not invent experience to fill a profile.

## 2. Read a market brief carefully

Open **Market brief** and request research when you want an update. The app uses preset role, city, and goal terms to search mainland China primary sources, then asks DeepSeek for a short brief.

The brief separates skill demand, market signals, pay evidence, and next steps. It includes source publication dates when available and a separate retrieval timestamp. A retrieval date means the app obtained material then; it does not prove the posting or policy is new.

This small search is not a representative labor-market survey. The pay section keeps your likely pay unknown. When a retrieved excerpt contains pay information, it can show that exact source sentence with its source ID and available publication date; this does not establish that the figure applies to your role, city, or experience. It does not estimate a graduate salary from aggregate wages. Missing, old, or unrelated evidence should remain visible. Review the linked posting for its city, degree requirements, graduation cohort, deadline, and working arrangement.

The official portals are useful starting points:

- [NCSS/24365](https://www.ncss.cn/) for student recruitment.
- [NCSS internships](https://www.ncss.cn/student/jobs/internindex.html) for internship discovery.
- [MOHRSS employment services](https://job.mohrss.gov.cn/) for public employment information.
- [National Bureau of Statistics](https://www.stats.gov.cn/) for aggregate data and methodology.

Some pages require browser interaction, login, or access the search service cannot obtain. A portal link remains a navigation aid even if no usable evidence can be retrieved. The app must not substitute an invented vacancy or salary.

Download a brief as Markdown to preserve its advice, source links, and available dates. Downloading does not trigger another research request.

## 3. Compare a job description

Under **Job tools**, paste up to 12,000 characters into **Job description** and select **Compare skills**. The tool runs locally against a small vocabulary of supported English and Chinese aliases.

The table shows:

- A skill mentioned in the submitted description.
- Whether you selected that skill in your saved profile.
- An excerpt from the posting so you can check the wording.
- A suggested exercise that could help you create tangible project evidence.

A mention can be optional or negated. For example, “SQL is not required” still mentions SQL. Read the excerpt before making it a priority. The catalog does not capture every technical tool, professional qualification, or industry-specific skill.

“Not selected” means absent from your self-reported profile. It does not prove you lack the ability. The tool does not score your resume, simulate an employer's ATS, or estimate your hiring chances.

Use one exercise as a starting point, then adjust it to your role and time. Keep portfolio evidence honest: explain the problem, your actual contribution, what you produced, and what you learned.

## 4. Keep an application tracker

Under **Track applications**, add company, role, city, status, optional deadline, optional HTTPS posting URL, and next-step notes. Status choices are Saved, Preparing, Applied, Assessment, Interview, Offer, Rejected, and Withdrawn.

Use **Update or remove a record** to change status and notes or remove an entry. There are no automatic applications, messages to recruiters, or deadline reminders.

Records stay in memory for the current session and are not sent to DeepSeek. Use **Download application CSV** before closing or refreshing. The file is your portable copy; store it where you normally keep personal documents.

To restore records, choose an exported CSV under **Import a tracker CSV**, then select **Replace records with CSV**. Import replaces the current list, so download it first if you want a separate copy. A failed import leaves the existing list intact.

The import supports UTF-8 CSV with the exported columns:

```text
id,company,role,city,status,deadline,job_url,notes
```

The limit is **200 records and 3 MB**. Dates use `YYYY-MM-DD`; optional values can be blank. Keep record IDs unchanged when editing an exported file. Invalid dates, unknown statuses, duplicate IDs, unexpected columns, or invalid URLs are rejected. Downloads neutralize formula-like cell starts for spreadsheet viewing; the importer restores the app's own escaping.

## 5. Discuss and download a plan

In **Career chat**, explain the decision you want help with. Your saved profile is supplied as background, so you can focus on the uncertainty or next task. Additional mentor styles remain available in the sidebar.

Once a conversation has enough context, open **Create a task plan**, choose 1–365 days, and select **Create checked plan**. The plan contains 3–8 tasks with timing, a reason, and a completion criterion. The app may request one correction if its structural checks fail.

**Task fields and schedule checked** confirms the required structure and schedule, plus source-reference checks. It is not a guarantee of factual accuracy, personal suitability, internship eligibility, or employment.

Use the plan's Markdown download to preserve the tasks and source record. A useful next step is small enough to complete and review, such as comparing three dated postings or producing one short project artifact.

## Connection and privacy

Online advice requires your own DeepSeek API key and available balance. Enter the key under **Connection** and select **Use for this session**. Research and replies may incur charges; no prepaid access is included.

When you ask for online advice, the saved profile and relevant conversation are sent to DeepSeek. Search receives only application-owned topic terms based on the selected role, city, and goal. The pasted job description and tracker do not leave the local tool merely because you use them. If you manually paste their contents into chat, that chat text is sent to the model.

Use **Permissions** to pause new online calls or reduce call limits. The app cannot recall an in-flight request, and request counts are not a spending limit. Profiles, chat, tracker records, and activity history are session-only. There is no account, cloud synchronization, or automatic restoration.

See the [Windows quick start](WINDOWS_QUICKSTART.md), [permissions guide](PERMISSIONS.md), and [source research record](STUDENT_CAREER_RESEARCH.md) for more detail.
