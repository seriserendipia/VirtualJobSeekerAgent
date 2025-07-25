import aiohttp
import asyncio

BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-From-Extension": "true"}

# 初始简历和 JD
resume = """Tinghuan Li
Tel: (+1)213-503-4998       Email: litinghuan0519@gmail.com      
LinkedIn: www.linkedin.com/in/tinghuanli
Education Background
University of Southern California (USC)                                                                                            Los Angeles, US                                                    
Master in Analytics     GPA: 3.92/4.0                                                                                                    08/2024－05/2026 (Expected)                                                        
Shanghai Lixin University of Accounting and Finance (SLU)                                                         Shanghai, China                                                      
Bachelor of Science in Data Science and Big Data Technology         GPA: 3.55/4.0 (top 10%)                             10/2020－07/2024                                                                           
Honor: University-level Scholarship ( top 10%);  Outstanding Graduate
Skills
Familiar with SQL and  Python framework (ipython and jupyter notebooks, Numpy, Pandas, Matplotlib, Sklearn, PyTorch, SciPy, Keras, Tensorflow, Matplotlib, seaborn, etc.) 
Experienced with Tableau, MATLAB, Linux environments, and major data platforms (including Hadoop, HBase, Spark).
Publication
Tinghuan Li. A Comparison of Deep Learning-based Object Detection for Unmanned Aerial Vehicle. The 4th International Conference on Signal Processing and Machine Learning (CONF-SPML 2024).
Internship Experience
Medcrab Technology Co., Ltd                                                                                                              Chengdu, China
Data Analyst Intern(Project Performance Management)                                                                                               04－06/2024
Analyzed project tracking data (100,000+ records) to enhance performance management, identifying key project phases and inefficiencies.
Cleaned data and selected features, incorporating phase durations and employee participation metrics.
Calculated variances between actual and expected timelines for project phases and individual employee work hours to identify delays and potential overages.
Built Tableau dashboards, using: Gantt charts for project timelines and phase deviations. Heatmaps for workload distribution and inefficiencies. Bar charts for planned vs. actual task completion. 
Uncovered issues related to inaccurate work records, unreasonable task allocations, and a lack of metrics for phase importance, leading to recommendations that improved operational efficiency.
Research & Projects
Research on ML-based Postoperative Stroke Risk Prediction in Elderly ICU Patients               04/2025－05/2025                                             
Queried 19,085 elderly ICU admissions from MIMIC-III/IV to study postoperative stroke risk;
Evaluated 8 machine learning classifiers using stratified 5-fold cross-validation and grid search; CatBoost achieved the highest AUROC (0.8868) on the held-out test set;
With only 20 selected features (vs. 42 in prior work, AUROC = 0.78), the model demonstrated improved performance and interpretability via SHAP and ablation analyses.
Research on Mortality Prediction in Sepsis-Associated ARDS with Machine Learning              01/2025－03/2025                                             
Queried 2,583 ICU stays from MIMIC-III using Sepsis-3 criteria, ARDS ICD codes, and clinical item IDs;
Developed a modular ML pipeline with ADASYN for class imbalance and evaluated 8 classifiers (e.g., LightGBM, SVM, RF) via stratified 5-fold CV with bootstrap confidence intervals;
LightGBM outperformed the benchmark RF model (AUROC = 0.8925 vs. 0.8015) using 13 vs. 24 features via embedded feature selection and hyperparameter tuning; results under manuscript preparation.
Research on Deep Learning-Based UAV Detection for Aviation Security                                     11/2023－03/2024                                             
Collected 3250 sample UAV images through web scraping, performed data labeling using LabelImg, and employed the Mosaic data augmentation technique to randomly scale, crop, and splice four training images;
Utilized YOLOv5s as the foundational model for training, integrating attention mechanisms SE and SimAM to enhance model performance. Achieved a detection precision of 89% with the YOLOv5s-SimAM model.
Developing User Movie Recommendation System                                                                                     04－06/2023
Developed a movie recommendation system by preprocessing over 270,000 user evaluation records and 100,000 movie entries, including handling missing data effectively;
Constructed a recall model using TF-IDF for vectorizing movie descriptions, calculating user historical average vectors, and measuring similarity to enhance initial movie selection;
Implemented a ranking model based on linear regression, creating training and testing datasets to predict user ratings for recalled movies and rank them accordingly. Integrated recall and ranking models to create a recommendation system that generates ten ranked movie suggestions tailored to diverse user profiles.
Modeling Strategies for Broad Telecom Users Portrait                                                                            01－03/2023
Collected and processed 60,000 data points from extensive telecom users using Hive, employing HiveQL for efficient querying and management of the data; 
Labeled user data to build comprehensive user profiles and developed a classification model utilizing the SVM algorithm to predict user retention potential, using these predictions as labels for user profiles. 
Implemented the ALS algorithm to recommend similar content to users.

"""
job_description = """About the job
Responsibilities
Trust and Safety Operations a pivotal team within U.S. Data Security. We strive to enable TikTok to become the most trusted and secure platform in the US through operational excellence in content moderation via innovations in technology, optimization in processes and investment in people. We ensure that we enforce our policies based on our community guidelines and we take appropriate actions in a timely manner to minimize risks on our platform to our users and advertisers.

As a Quality Data Analyst within TikTok's USDS Training and Quality team reporting to the Quality Manager, you will be a key member of our Trust and Safety operations. In this role, you will:
- Empower Decision-Making: Own and maintain data systems and dashboards, ensuring that QA results are accurate and readily available as vital business intelligence for both internal and external teams.
- Drive Quality Processes: Execute high-quality audit processes and deliver actionable insights to stakeholders, contributing to continuous quality program enhancements.
- Conduct In-Depth Analyses: Perform system-wide root cause analyses (RCA) for Trust and Safety moderation queues and manage data validation processes to identify and address areas for improvement.
- Lead Data Management: Take charge of the quality team’s data management, ensuring robust data integrity that supports strategic decision-making across the organization.
This role combines technical expertise with a strong analytical mindset, making you a key driver in enhancing our Trust and Safety initiatives.

In order to enhance collaboration and cross-functional partnerships, among other things, at this time, our organization follows a hybrid work schedule that requires employees to work in the office 3 days a week, or as directed by their manager/department. We regularly review our hybrid work model, and the specific requirements may change at any time.

Responsibilities: 
- Own and maintain backend data systems ensuring data quality, accuracy, and consistency across multiple sources.
- Design, build, and maintain intuitive dashboards and data tables that monitor key trust and safety metrics, enabling proactive issue detection and decision-making.
- Develop, document, and continually refine data-related processes and workflows; ensure data processes align with broader trust and safety strategies.
- Conduct deep-dive analyses to identify trends, anomalies, and actionable insights; communicate findings to cross-functional teams to drive strategic improvements.
- Partner with crossfunctional teams to ensure data solutions support operational needs 
- Support in the implementation of audits and monitoring systems to uphold data integrity and support adherence to moderation accuracy
- Provide timely insights through reports and analyses on Accuracy trends and performance

Qualifications
Minimum Qualifications
- 3+ years experience in Trust & Safety, or similar industry experience
- Experience creating analysis reports and conducting RCAs
- Creative, solution-oriented mindset with the ability to execute under pressure and meet deadlines
- Able to work with minimal supervision, taking ownership of work and completing tasks in a timely manner, while adapting rapidly to changing work environments, priorities and organizational needs
- Ability to provide data driven analysis to cross functional teams in various processes, policies, and procedures
- SQL skills for querying and manipulating large datasets.
- Experience with dashboarding and data visualization tools (e.g., Tableau, PowerBI).

Preferred Qualifications
- Great at working cross-functionally with other teams/departments
- Exceptional verbal and written communication skills
- At least 3 years of people management skills
- Direct experience conducting research and analyzing data to gain insights into the business

Wellbeing Statement
Trust & Safety recognizes that keeping our platform safe for TikTok communities is no ordinary job. It can be rewarding, psychologically demanding, and emotionally taxing. This is why we are sharing the potential hazards, risks and implications in this unique line of work from the start: so our candidates are well informed before proceeding.

We are committed to the wellbeing of all our employees and promise to provide comprehensive and evidence-based programs, to promote and support physical and mental wellbeing throughout each employee's journey with us. We believe that wellbeing is a relationship and that everyone has a part to play, so we work in collaboration and consultation with our employees and across our functions in order to ensure a truly person-centred, innovative and integrated approach.

About USDS
TikTok is the leading destination for short-form mobile video. Our mission is to inspire creativity and bring joy. U.S. Data Security (“USDS”) is a subsidiary of TikTok in the U.S. This new, security-first division was created to bring heightened focus and governance to our data protection policies and content assurance protocols to keep U.S. users safe. Our focus is on providing oversight and protection of the TikTok platform and U.S. user data, so millions of Americans can continue turning to TikTok to learn something new, earn a living, express themselves creatively, or be entertained. The teams within USDS that deliver on this commitment daily span across Trust & Safety, Security & Privacy, Engineering, User & Product Ops, Corporate Functions and more.

Data Security Statement
This role requires the ability to work with and support systems designed to protect sensitive data and information. As such, this role will be subject to strict national security-related screening.


Why Join Us
Inspiring creativity is at the core of TikTok's mission. Our innovative product is built to help people authentically express themselves, discover and connect – and our global, diverse teams make that possible. Together, we create value for our communities, inspire creativity and bring joy - a mission we work towards every day.
We strive to do great things with great people. We lead with curiosity, humility, and a desire to make impact in a rapidly growing tech company. Every challenge is an opportunity to learn and innovate as one team. We're resilient and embrace challenges as they come. By constantly iterating and fostering an "Always Day 1" mindset, we achieve meaningful breakthroughs for ourselves, our company, and our users. When we create and grow together, the possibilities are limitless. Join us.

Diversity & Inclusion
TikTok is committed to creating an inclusive space where employees are valued for their skills, experiences, and unique perspectives. Our platform connects people from across the globe and so does our workplace. At TikTok, our mission is to inspire creativity and bring joy. To achieve that goal, we are committed to celebrating our diverse voices and to creating an environment that reflects the many communities we reach. We are passionate about this and hope you are too.


USDS Reasonable Accommodation
USDS is committed to providing reasonable accommodations in our recruitment processes for candidates with disabilities, pregnancy, sincerely held religious beliefs or other reasons protected by applicable laws. If you need assistance or a reasonable accommodation, please reach out to us at https://tinyurl.com/USDS-RA


Job Information
【For Pay Transparency】Compensation Description (Annually)
The base salary range for this position in the selected city is $83600 - $135111 annually.
Compensation may vary outside of this range depending on a number of factors, including a candidate’s qualifications, skills, competencies and experience, and location. Base pay is one part of the Total Package that is provided to compensate and recognize employees for their work, and this role may be eligible for additional discretionary bonuses/incentives, and restricted stock units.
Benefits may vary depending on the nature of employment and the country work location. Employees have day one access to medical, dental, and vision insurance, a 401(k) savings plan with company match, paid parental leave, short-term and long-term disability coverage, life insurance, wellbeing benefits, among others. Employees also receive 10 paid holidays per year, 10 paid sick days per year and 17 days of Paid Personal Time (prorated upon hire with increasing accruals by tenure).
The Company reserves the right to modify or change these benefits programs at any time, with or without notice.
For Los Angeles County (unincorporated) Candidates:
Qualified applicants with arrest or conviction records will be considered for employment in accordance with all federal, state, and local laws including the Los Angeles County Fair Chance Ordinance for Employers and the California Fair Chance Act. Our company believes that criminal history may have a direct, adverse and negative relationship on the following job duties, potentially resulting in the withdrawal of the conditional offer of employment:
1. Interacting and occasionally having unsupervised contact with internal/external clients and/or colleagues;
2. Appropriately handling and managing confidential information including proprietary and trade secret information and access to information technology systems; and
3. Exercising sound judgment.

Benefits found in job post

401(k)
Vision insurance
Disability insurance"""

# 多轮用户指令，可自行添加
user_prompts = [
    "请让语气更正式",
    "再简洁一点",
    "加一句我会 Python 和 SQL",
]

# 最终确认接收方邮箱
final_email_to = "lizhuoya@usc.edu"


# 用于保存当前内容
current_email_content = ""


async def generate_email(prompt=None):
    global current_email_content

    payload = {
        "resume": resume,
        "job_description": job_description,
    }
    if prompt:
        payload["user_prompt"] = prompt

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/generate_email", headers=HEADERS, json=payload) as response:
            result = await response.json()
            email_text = result.get("final_output") or result.get("generated_email")
            print("\n📧 Generated Email Content:")
            print(email_text)
            current_email_content = email_text  # 更新当前内容


async def revise_email(instruction):
    global current_email_content

    payload = {
        "original_email": current_email_content,
        "instruction": instruction,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/revise_email", headers=HEADERS, json=payload) as response:
            result = await response.json()
            revised = result.get("revised_email")
            print(f"\n🔁 Revised with instruction '{instruction}':")
            print(revised)
            current_email_content = revised  # 更新当前内容


async def send_final_email():
    email_data = {
        "to": final_email_to,
        "subject": "跟进求职邮件",
        "body": current_email_content
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/send-email", headers=HEADERS, json=email_data) as response:
            result = await response.json()
            print("\n🚀 Send Result:")
            print(result)


async def main():
    print("🚦 Initial email generation...")
    await generate_email()

    for idx, prompt in enumerate(user_prompts):
        print(f"\n⏳ Round {idx + 1}: {prompt}")
        await asyncio.sleep(1)
        await revise_email(prompt)

    print("\n✅ Final Confirmation: Sending email...")
    await send_final_email()


if __name__ == "__main__":
    asyncio.run(main())