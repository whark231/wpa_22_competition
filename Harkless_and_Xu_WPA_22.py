# -*- coding: utf-8 -*-
"""Wharton Competion

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KhgaZP0hUAkIyefV5J-aIKMUabx469ca
"""

import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder

!pip install pandasql
import pandasql as ps

#Load in CSV's
from google.colab import drive
drive.mount('/content/drive')

headcount_df = pd.read_csv("/content/drive/MyDrive/Competition/WDC_HEADCOUNT.csv")
person_df = pd.read_csv("/content/drive/MyDrive/Competition/WDC_PERSON.csv")
termination_df = pd.read_csv("/content/drive/MyDrive/Competition/WDC_TERMINATION.csv")
term_sum_df = pd.read_csv("/content/drive/MyDrive/Competition/WDC_terminat_summary.csv")

headcount_df.head()

headcount_df["full_time_flag"] = headcount_df["full_part_time"] == "Full-Time"

headcount_df["EXEMPT_FLAG"] = headcount_df["EXEMPT_NONEXEMPT"] == "E"
jobs_encoded = pd.get_dummies(headcount_df["job_function"])

headcount_df["salary_change"] = headcount_df["salary_change"].fillna('same')
salary_encoded = pd.get_dummies(headcount_df["salary_change"], prefix = "salary")

home_encoded = pd.get_dummies(headcount_df["home_location"], prefix = "home")

headcount_df["main_campus_flag"] = headcount_df["work_location"] == "main_campus"

org_encoded = pd.get_dummies(headcount_df["ORG_CODE"])

headcount_df = pd.concat([headcount_df, jobs_encoded, salary_encoded, home_encoded, org_encoded], axis = 1)
headcount_df

person_df.head()

for col in person_df.columns:
  print(col + ": " + str(person_df[col].unique()))

person_df = person_df.dropna(subset = ["PERSON_ID_EMPLOYEE"], axis = 0)
person_df["age_ventile"] = person_df["age_ventile"].apply(lambda x: int(x[:2]) if len(x) > 2 else int(x[0]))
sex_encoded = pd.get_dummies(person_df["sex_A_B"], prefix = "sex")
race_encoded = pd.get_dummies(person_df["race"])
person_df["married_T_F"] = person_df["married_T_F"] == "married_A"
rep_encoded = pd.get_dummies(person_df["Drct_Rprt_ct"], prefix = "rep")
person_df["highest_degree"] = person_df["highest_degree"].fillna("0")
person_df["highest_degree"] = person_df["highest_degree"].apply(lambda x: int(x[0]))
person_df = pd.concat([person_df, sex_encoded, race_encoded, rep_encoded], axis = 1)

person_df

termination_df.head()

for col in termination_df.columns:
  print(col + ": " + str(termination_df[col].unique()))

termination_df["invol_terminat"] = termination_df["invol_terminat"] == "Yes"
reason_encoded = pd.get_dummies(termination_df["terminate_reason"], prefix = "reason")
termination_df = pd.concat([termination_df, reason_encoded], axis = 1)

termination_df

term_sum_df.head()

"""# Data Cleaning and Wrangling"""

# Contains all information for any worker terminated in time frame

terms_info_df = pd.merge(termination_df, headcount_df, on = ['PERSON_ID_EMPLOYEE'], how = 'left').drop(['report_year', 'report_month'], axis = 1).drop_duplicates()
terms_info_df = terms_info_df.merge(person_df, on = ['PERSON_ID_EMPLOYEE'], how = 'left')
terms_info_df

# Contains info for all workers whose 'involuntary termination' flag is not YES

resig_info_df = terms_info_df[terms_info_df['invol_terminat'] != 'Yes'].reset_index(drop = True).drop(['invol_terminat'], axis = 1)
resig_info_df

resig_info_df.columns

headcount_df

headcount_detail_df = headcount_df.merge(person_df, on = ['PERSON_ID_EMPLOYEE'], how = 'left')
headcount_detail_df['salary_change'] = headcount_detail_df['salary_change'].apply(lambda x: 1 if x == 'increase' else 0)
headcount_detail_df['home_is_work'] = headcount_detail_df['home_is_work'].apply(lambda x: 1 if x == True else 0)
headcount_detail_df['full_part_time'] = headcount_detail_df['full_part_time'].apply(lambda x: 1 if x == 'Full-Time' else 0)

headcount_detail_df

from datetime import datetime

def f(month, year):
  datestring = f'{month}-{year}'
  return datetime.strptime(datestring, "%m-%Y")

term_sum_df['date'] = term_sum_df.apply(lambda x: f(x.terminat_month, x.terminat_year), axis=1)

term_sum_df = term_sum_df.sort_values(by = ['date']).reset_index()
term_sum_df['percent_termin_voluntary'] = term_sum_df['termin_voluntary']/term_sum_df['staff_tot']
term_sum_df['avg_termin_voluntary'] = term_sum_df['percent_termin_voluntary'].rolling(12).mean()
term_sum_df.head()

"""# Visualization"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pyplot import figure
plt.style.use('ggplot')

figure(figsize=(12, 8), dpi=80)

plt.plot(term_sum_df['date'], term_sum_df['avg_termin_voluntary'])
plt.xlabel('Year')
plt.ylabel('Percent of Workforce Vonluntarily Terminating')
plt.title('Rolling Average of Percent of Workforce Voluntarily Terminating')

headcount_monthly_df = headcount_detail_df.groupby(by = ['report_year', 'report_month', 'sex_A']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Total_Headcount"})
headcount_monthly_df

resig_monthly_df = resig_info_df.groupby(by = ['termination_year', 'termination_month', 'sex_A']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Termination_Count"})
resig_monthly_df

resig_sex = pd.concat([headcount_monthly_df, resig_monthly_df],axis=1).dropna()
resig_sex['Percent_Resig'] = resig_sex['Termination_Count'] / resig_sex['Total_Headcount']
resig_sex.reset_index(inplace = True)
resig_sex = resig_sex.rename(columns = {'level_0': 'Year', 'level_1': 'Month'})
resig_sex['Date'] = resig_sex.apply(lambda x: f(int(x.Month), int(x.Year)), axis=1)

resig_sex_totals = resig_sex.groupby(['sex_A']).sum()
resig_sex_totals['Percent_Resig'] = resig_sex_totals['Termination_Count'] / resig_sex_totals['Total_Headcount']
resig_sex_totals = resig_sex_totals.drop(['Year', 'Month'], axis = 1)
resig_sex_totals = resig_sex_totals.reset_index()
resig_sex_totals

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.style.use('ggplot')
figure(figsize=(10, 6), dpi=80)

sex = [1, 0]
count = [resig_sex_totals[resig_sex_totals['sex_A'] == x]['Percent_Resig'].values[0] for x in sex]

x_pos = [i for i, _ in enumerate(sex)]

plt.bar(x_pos, count, color=['red', 'blue'])
plt.xlabel("Sex")
plt.ylabel("Resignation Percentage per Person-Month")
plt.title("Resignation Fraction per Person-Month Based on Sex")

plt.xticks(x_pos, ['Sex A', 'Sex B'])

plt.show()

sex_0_df = resig_sex[resig_sex['sex_A'] == 0]
sex_1_df = resig_sex[resig_sex['sex_A'] == 1]
plt.style.use('ggplot')

figure(figsize=(12, 8), dpi=80)
plt.plot(sex_1_df['Date'], sex_1_df['Percent_Resig'], label = 'Sex A')
plt.plot(sex_0_df['Date'], sex_0_df['Percent_Resig'], label = 'Sex B')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Percent of Workforce Terminating (Voluntary)')
plt.title('Workforce Termination Rates Based on Sex')

person_df.columns

resig_monthly_df = resig_info_df.groupby(by = ['termination_year', 'termination_month', 'race']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Termination_Count"})
headcount_monthly_df = headcount_detail_df.groupby(by = ['report_year', 'report_month', 'race']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Total_Headcount"})

resig_race = pd.concat([headcount_monthly_df, resig_monthly_df],axis=1).dropna()
resig_race['Percent_Resig'] = resig_race['Termination_Count'] / resig_race['Total_Headcount']
resig_race.reset_index(inplace = True)
resig_race = resig_race.rename(columns = {'level_0': 'Year', 'level_1': 'Month'})
resig_race['Date'] = resig_race.apply(lambda x: f(int(x.Month), int(x.Year)), axis=1)

resig_race

resig_race_totals = resig_race.groupby(['race']).sum()
resig_race_totals['Percent_Resig'] = resig_race_totals['Termination_Count'] / resig_race_totals['Total_Headcount']
resig_race_totals = resig_race_totals.drop(['Year', 'Month'], axis = 1)
resig_race_totals = resig_race_totals.reset_index()
resig_race_totals['race'] = resig_race_totals['race'].apply(lambda x: x.replace(" ", "_"))
resig_race_totals

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.style.use('ggplot')
figure(figsize=(10, 6), dpi=80)

race_letters = ['A', 'B', 'C', 'D']
race = ["race_" + x for x in race_letters]
count = [resig_race_totals[resig_race_totals['race'] == x]['Percent_Resig'].values[0] for x in race]

x_pos = [i for i, _ in enumerate(race)]

plt.bar(x_pos, count, color=['red', 'blue', 'purple', 'gray'])
plt.xlabel("Race")
plt.ylabel("Resignation Percentage per Person-Month")
plt.title("Resignation Fraction per Person-Month Based on Sex")

plt.xticks(x_pos, race)

plt.show()

figure(figsize=(12, 8), dpi=80)
plt.plot(resig_race[resig_race['race'] == 'race A']['Date'], resig_race[resig_race['race'] == 'race A']['Percent_Resig'], label = 'Race A')
plt.plot(resig_race[resig_race['race'] == 'race_B']['Date'], resig_race[resig_race['race'] == 'race_B']['Percent_Resig'], label = 'Race B')
plt.plot(resig_race[resig_race['race'] == 'race_C']['Date'], resig_race[resig_race['race'] == 'race_C']['Percent_Resig'], label = 'Race C')
plt.plot(resig_race[resig_race['race'] == 'race_D']['Date'], resig_race[resig_race['race'] == 'race_D']['Percent_Resig'], label = 'Race D')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Percent of Workforce Terminating (Voluntary)')
plt.title('Workforce Termination Rates Based on Race')

resig_monthly_df = resig_info_df.groupby(by = ['termination_year', 'termination_month', 'age_ventile']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Termination_Count"})
headcount_monthly_df = headcount_detail_df.groupby(by = ['report_year', 'report_month', 'age_ventile']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Total_Headcount"})

resig_age = pd.concat([headcount_monthly_df, resig_monthly_df],axis=1).dropna()
resig_age['Percent_Resig'] = resig_age['Termination_Count'] / resig_age['Total_Headcount']
resig_age.reset_index(inplace = True)
resig_age = resig_age.rename(columns = {'level_0': 'Year', 'level_1': 'Month'})
resig_age['Date'] = resig_age.apply(lambda x: f(int(x.Month), int(x.Year)), axis=1)

resig_age

resig_age_totals = resig_age.groupby(['age_ventile']).sum()
resig_age_totals['Percent_Resig'] = resig_age_totals['Termination_Count'] / resig_age_totals['Total_Headcount']
resig_age_totals = resig_age_totals.drop(['Year', 'Month'], axis = 1)
resig_age_totals = resig_age_totals.reset_index()
resig_age_totals

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.style.use('ggplot')
figure(figsize=(10, 6), dpi=80)

ages = [i*5 for i in range(1, 18)]
count = [resig_age_totals[resig_age_totals['age_ventile'] == x]['Percent_Resig'].values[0] for x in ages]

x_pos = [i for i, _ in enumerate(ages)]

plt.bar(x_pos, count, color='green')
plt.xlabel("Age Ventile")
plt.ylabel("Resignation Percentage per Person-Month")
plt.title("Resignation Fraction per Person-Month for Age Ventiles")

plt.xticks(x_pos, ages)

plt.show()

figure(figsize=(12, 8), dpi=80)

plt.plot(resig_age[resig_age['age_ventile'] == 15]['Date'], resig_age[resig_age['age_ventile'] == 15]['Percent_Resig'], label = f'Ventile {15}')
plt.plot(resig_age[resig_age['age_ventile'] == 60]['Date'], resig_age[resig_age['age_ventile'] == 60]['Percent_Resig'], label = f'Ventile {60}')

plt.legend()
plt.xlabel('Date')
plt.ylabel('Percent of Workforce Terminating (Voluntary)')
plt.title('Workforce Termination Rates Based on Age Ventile')

resig_monthly_df = resig_info_df.groupby(by = ['termination_year', 'termination_month', 'salary_decile']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Termination_Count"})
headcount_monthly_df = headcount_detail_df.groupby(by = ['report_year', 'report_month', 'salary_decile']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Total_Headcount"})

resig_sal = pd.concat([headcount_monthly_df, resig_monthly_df],axis=1).dropna()
resig_sal['Percent_Resig'] = resig_sal['Termination_Count'] / resig_sal['Total_Headcount']
resig_sal.reset_index(inplace = True)
resig_sal = resig_sal.rename(columns = {'level_0': 'Year', 'level_1': 'Month'})
resig_sal['Date'] = resig_sal.apply(lambda x: f(int(x.Month), int(x.Year)), axis=1)

resig_sal

resig_sal_totals = resig_sal.groupby(['salary_decile']).sum()
resig_sal_totals['Percent_Resig'] = resig_sal_totals['Termination_Count'] / resig_sal_totals['Total_Headcount']
resig_sal_totals = resig_sal_totals.drop(['Year', 'Month'], axis = 1)
resig_sal_totals = resig_sal_totals.reset_index()
resig_sal_totals

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.style.use('ggplot')
figure(figsize=(10, 6), dpi=80)

deciles = [i*10 for i in range(1, 11)]
count = [resig_sal_totals[resig_sal_totals['salary_decile'] == x]['Percent_Resig'].values[0] for x in deciles]

x_pos = [i for i, _ in enumerate(deciles)]

plt.bar(x_pos, count, color='green')
plt.xlabel("Salary Decile")
plt.ylabel("Resignation Percentage per Person-Month")
plt.title("Resignation Fraction per Person-Month for Salary Deciles")

plt.xticks(x_pos, deciles)

plt.show()

figure(figsize=(12, 8), dpi=80)

for i in range(1, 3):
  plt.plot(resig_sal[resig_sal['salary_decile'] == i*10]['Date'], resig_sal[resig_sal['salary_decile'] == i*10]['Percent_Resig'], label = f'Decile {i*10}')
for i in range(9, 11):
  plt.plot(resig_sal[resig_sal['salary_decile'] == i*10]['Date'], resig_sal[resig_sal['salary_decile'] == i*10]['Percent_Resig'], label = f'Decile {i*10}')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Percent of Workforce Terminating (Voluntary)')
plt.title('Workforce Termination Rates Based on Salary Decile')

resig_monthly_df = resig_info_df.groupby(by = ['termination_year', 'termination_month', 'job_function']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Termination_Count"})
headcount_monthly_df = headcount_detail_df.groupby(by = ['report_year', 'report_month', 'job_function']).count()[['PERSON_ID_EMPLOYEE']].rename(columns={"PERSON_ID_EMPLOYEE": "Total_Headcount"})
resig_job = pd.concat([headcount_monthly_df, resig_monthly_df],axis=1).dropna()
resig_job['Percent_Resig'] = resig_job['Termination_Count'] / resig_job['Total_Headcount']
resig_job.reset_index(inplace = True)
resig_job = resig_job.rename(columns = {'level_0': 'Year', 'level_1': 'Month'})
resig_job['Date'] = resig_job.apply(lambda x: f(int(x.Month), int(x.Year)), axis=1)

resig_job

resig_job_totals = resig_job.groupby(['job_function']).sum()
resig_job_totals['Percent_Resig'] = resig_job_totals['Termination_Count'] / resig_job_totals['Total_Headcount']
resig_job_totals = resig_job_totals.drop(['Year', 'Month'], axis = 1)
resig_job_totals = resig_job_totals.reset_index()
resig_job_totals

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.style.use('ggplot')
figure(figsize=(10, 6), dpi=80)

jobs = ['B', 'C', 'D', 'F', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'S']
jobs = ['job_' + x for x in jobs]
count = [resig_job_totals[resig_job_totals['job_function'] == x]['Percent_Resig'].values[0] for x in jobs]

x_pos = [i for i, _ in enumerate(jobs)]

plt.bar(x_pos, count, color='green')
plt.xlabel("Job Function")
plt.ylabel("Resignation Percentage")
plt.title("Resignation Fraction per Person-Month")

plt.xticks(x_pos, jobs)

plt.show()

figure(figsize=(12, 8), dpi=80)
plt.plot(resig_job[resig_job['job_function'] == 'job_C']['Date'], resig_job[resig_job['job_function'] == 'job_C']['Percent_Resig'], label = 'Job C')
plt.plot(resig_job[resig_job['job_function'] == 'job_F']['Date'], resig_job[resig_job['job_function'] == 'job_F']['Percent_Resig'], label = 'Job F')
plt.plot(resig_job[resig_job['job_function'] == 'job_J']['Date'], resig_job[resig_job['job_function'] == 'job_J']['Percent_Resig'], label = 'Job J')
plt.plot(resig_job[resig_job['job_function'] == 'job_M']['Date'], resig_job[resig_job['job_function'] == 'job_M']['Percent_Resig'], label = 'Job M')



plt.legend()
plt.xlabel('Date')
plt.ylabel('Percent of Workforce Terminating (Voluntary)')
plt.title('Workforce Termination Rates Based on Job')

"""# Modeling"""

data_df = headcount_detail_df.select_dtypes(['number']).drop(['salary_change', 'salary_same', 'ON_LEAVE_FLAG', 'ON_FMLA_LEAVE_FLAG', 'report_year', 'report_month'], axis = 1).drop_duplicates(subset = 'PERSON_ID_EMPLOYEE', keep = 'last').reset_index(drop = True)

data_df.columns

from sklearn.model_selection import train_test_split

data = data_df.merge(resig_info_df[['PERSON_ID_EMPLOYEE']], on = ['PERSON_ID_EMPLOYEE'], how = 'outer', indicator = "Resigned")
data['Resigned'] = data['Resigned'].apply(lambda x: 0 if x == 'left_only' else 1)
#data = data[['PERSON_ID_EMPLOYEE', 'age_ventile', 'married_T_F', 'highest_degree', 'sex_A', 'sex_B', 'race A', 'race_B', 'race_C', 'race_D', 'rep_1_1DR', 'rep_2_2-5DR', 'rep_3_6-9DR', 'rep_4_10+DR', 'Resigned']]
data = data.dropna()
data = data.drop(['PERSON_ID_EMPLOYEE'], axis = 1)

X = data[['full_part_time', 'home_is_work', 'salary_decile',
       'job_B', 'job_C', 'job_D', 'job_F', 'job_H', 'job_I', 'job_J', 'job_K',
       'job_L', 'job_M', 'job_N', 'job_O', 'job_P', 'job_Q', 'job_S',
       'salary_increase', 'salary_large', 'home_Ex_Region', 'home_Phila',
       'home_Phila_MSA', 'Org_1010', 'Org_1011', 'Org_1013', 'Org_1014',
       'Org_1016', 'Org_1017', 'Org_1019', 'Org_1021', 'Org_1024', 'Org_1025',
       'Org_1026', 'Org_1029', 'Org_1030', 'Org_1035', 'Org_1036', 'Org_1039',
       'Org_1040', 'age_ventile', 'highest_degree', 'sex_A', 'sex_B', 'race A',
       'race_B', 'race_C', 'race_D', 'rep_1_1DR', 'rep_2_2-5DR', 'rep_3_6-9DR',
       'rep_4_10+DR']]
y = data[['Resigned']]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

corr = data.corr()[['Resigned']].sort_values(by = ['Resigned'], ascending = False)
plt.figure(figsize=(16, 12))
sns.heatmap(corr, annot = True)

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, recall_score, precision_score
from sklearn.svm import SVC

from sklearn.linear_model import RidgeClassifier, RidgeClassifierCV
from sklearn.decomposition import PCA
from sklearn import preprocessing

# Statistics
import statsmodels.formula.api as smf
import statsmodels.api as sm

def model_info(mod, x, y, name, typem):
  accs = (accuracy_score(y, mod.predict(x)), recall_score(y, mod.predict(x)), precision_score(y, mod.predict(x)))
  result = f"{name} {typem} data: accuracy = {str(round(accs[0], 3))}, recall = {str(round(accs[1], 3))}, precision = {str(round(accs[2], 3))}"
  return result

clf_logistic = LogisticRegression().fit(X_train, y_train.values.ravel()) # BEST MODEL FOR LOGISTIC REGRESSION
l1_logit = LogisticRegression(penalty = 'l1', solver = 'saga').fit(X_train, y_train.values.ravel())
l2_logit = LogisticRegression(penalty = 'l2').fit(X_train, y_train.values.ravel())
elastic_logit = LogisticRegression(penalty = 'elasticnet', solver = 'saga', l1_ratio = 0.5).fit(X_train, y_train.values.ravel())
clf_logit = LogisticRegression(penalty = 'none').fit(X_train, y_train.values.ravel())

print(model_info(clf_logistic, X_train, y_train.values.ravel(), "clf_logistic", "train"))
print(model_info(clf_logistic, X_test, y_test, "clf_logistic", "test"))
print("\n")
print(model_info(l1_logit, X_train, y_train.values.ravel(), "l1_logit", "train"))
print(model_info(l1_logit, X_test, y_test, "l1_logit", "test"))
print("\n")
print(model_info(l2_logit, X_train, y_train.values.ravel(), "l2_logit", "train"))
print(model_info(l2_logit, X_test, y_test, "l2_logit", "test"))
print("\n")
print(model_info(elastic_logit, X_train, y_train.values.ravel(), "elastic_logit", "train"))
print(model_info(elastic_logit, X_test, y_test, "elastic_logit", "test"))
print("\n")
print(model_info(clf_logit, X_train, y_train.values.ravel(), "clf_logit", "train"))
print(model_info(clf_logit, X_test, y_test, "clf_logit", "test"))

alphas = np.linspace(10 ** 1, 10 ** 3, 100)
ridgecv = RidgeClassifierCV(alphas = alphas, scoring = 'neg_mean_squared_error', normalize = True, cv = 10)
ridgecv.fit(X_train, y_train.values.ravel())
ridge_select = ridgecv.alpha_
ridge = RidgeClassifier(alpha = ridge_select, normalize = True).fit(X_train, y_train.values.ravel())

print(model_info(ridge, X_train, y_train.values.ravel(), "ridge", "train"))
print(model_info(ridge, X_test, y_test, "ridge", "test"))

"""## Trees"""

from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, KFold
from sklearn.tree import DecisionTreeClassifier
from sklearn.decomposition import PCA
from sklearn import preprocessing
from sklearn.feature_selection import RFE

"""Gradient Boosting Classifier """

params = {'max_depth': np.arange(3, 21)}
grid_search_cv =  GridSearchCV(GradientBoostingClassifier(random_state = 42), params, n_jobs = -1)
grid_search_cv.fit(X_train, y_train.values.ravel())
max_depth = grid_search_cv.best_params_['max_depth']
print(max_depth)

gcv_xgb = GradientBoostingClassifier(max_depth = 14, random_state = 42).fit(X_train, y_train.values.ravel())
clf_xgb = GradientBoostingClassifier(random_state = 42).fit(X_train, y_train.values.ravel())

"""Random Forest Classifier"""

params = {'max_depth': np.arange(3, 21), 'n_estimators': [75, 100, 150, 200]}
grid_search_cv =  GridSearchCV(RandomForestClassifier(random_state = 42), params, n_jobs = -1)
grid_search_cv.fit(X_train, y_train.values.ravel())
max_depth = grid_search_cv.best_params_['max_depth']
print(max_depth)
print(grid_search_cv.best_params_)

gcv_rfc = RandomForestClassifier(max_depth = 20, n_estimators = 200, random_state = 42).fit(X_train, y_train.values.ravel())
clf_rfc = RandomForestClassifier(random_state = 42).fit(X_train, y_train.values.ravel())

print(model_info(gcv_xgb, X_train, y_train.values.ravel(), "Gradient Boosting CV", "train"))
print(model_info(gcv_xgb, X_test, y_test, "Gradient Boosting CV", "test"))
print("\n")
print(model_info(clf_xgb, X_train, y_train.values.ravel(), "Gradient Boosting", "train"))
print(model_info(clf_xgb, X_test, y_test, "Gradient Boosting", "test"))
print("\n")
print(model_info(gcv_rfc, X_train, y_train.values.ravel(), "Random Forest CV", "train"))
print(model_info(gcv_rfc, X_test, y_test, "Random Forest CV", "test"))
print("\n")
print(model_info(clf_rfc, X_train, y_train.values.ravel(), "Random Forest", "train"))
print(model_info(clf_rfc, X_test, y_test, "Random Forest", "test"))

feature_importance = clf_rfc.feature_importances_
feature_names = clf_rfc.feature_names_in_
feature_names = [x for _,x in sorted(zip(feature_importance, feature_names), key=lambda pair: pair[0])]
feature_importance.sort()
feature_importance = feature_importance[-10:]
feature_names = feature_names[-10:]

fig, ax = plt.subplots()   
fig.set_size_inches(12, 8)
width = 0.75 # the width of the bars 
ind = np.arange(len(feature_importance))  # the x locations for the groups
ax.barh(ind, feature_importance, width, color="blue")
ax.set_yticks(ind + width/2)
ax.set_yticklabels(feature_names, minor=False)
plt.title('Feature Importance For Random Forest Classifier')
plt.xlabel('Relative Importance')
plt.ylabel('Feature Name')

from sklearn import tree

fn=X_train.columns
cn=["No Resign", "Resign"]
fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
tree.plot_tree(clf_rfc.estimators_[0],
               feature_names = fn, 
               class_names=cn,
               filled = True);
#fig.savefig('rf_individualtree.png')

feature_importance = gcv_xgb.feature_importances_
feature_names = gcv_xgb.feature_names_in_
feature_names = [x for _,x in sorted(zip(feature_importance, feature_names), key=lambda pair: pair[0])]
feature_importance.sort()
feature_importance = feature_importance[-10:]
feature_names = feature_names[-10:]

fig, ax = plt.subplots()    
fig.set_size_inches(12, 8)
width = 0.75 # the width of the bars 
ind = np.arange(len(feature_importance))  # the x locations for the groups
ax.barh(ind, feature_importance, width, color="red")
ax.set_yticks(ind + width/2)
ax.set_yticklabels(feature_names, minor=False)
plt.title('Feature Importance For Gradient Boosting CV Classifier')
plt.xlabel('Relative Importance')
plt.ylabel('Feature Name')

"""# Applying PCA"""

X_train_scaled = preprocessing.StandardScaler().fit_transform(X_train)
X_train_red = PCA(n_components = 10).fit_transform(X_train_scaled)

X_test_scaled = preprocessing.StandardScaler().fit_transform(X_test)
X_test_red = PCA(n_components = 10).fit_transform(X_test_scaled)

"""SVC with PCA

SVC
"""

Cs = [0.001, 0.01, 0.1, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 10]
gammas = [0.001, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.2, 1]
degrees = [0.5, 1, 2, 3, 4, 5]
poly_param_grid = {'degree': degrees}
param_grid = {'C': Cs, 'gamma' : gammas}

clf_svm = SVC(random_state = 42).fit(X_train_red, y_train.values.ravel())

print(model_info(clf_svm, X_train_red, y_train.values.ravel(), "SVC", "train"))
print(model_info(clf_svm, X_test_red, y_test, "SVC", "test"))

linear_svc = SVC(kernel='linear', random_state = 42)
rbf_svc = SVC(kernel = 'rbf', random_state = 42)
poly_svc = SVC(kernel='poly', random_state=42)

linear_svm_basic = SVC(kernel='linear', random_state = 42).fit(X_train_red, y_train.values.ravel())
rbf_svm_basic = SVC(kernel = 'rbf', random_state = 42).fit(X_train_red, y_train.values.ravel())
poly_svm_basic = SVC(kernel='poly', random_state=42).fit(X_train_red, y_train.values.ravel())

print(model_info(linear_svm_basic, X_train_red, y_train.values.ravel(), "linear_svm_basic", "train"))
print(model_info(linear_svm_basic, X_test_red, y_test, "linear_svm_basic", "test"))
print("\n")
print(model_info(rbf_svm_basic, X_train_red, y_train.values.ravel(), "rbf_svm_basic", "train"))
print(model_info(rbf_svm_basic, X_test_red, y_test, "rbf_svm_basic", "test"))
print("\n")
print(model_info(poly_svm_basic, X_train_red, y_train.values.ravel(), "poly_svm_basic", "train"))
print(model_info(poly_svm_basic, X_test_red, y_test, "poly_svm_basic", "test"))

"""Linear SVC"""

linear_clf = RandomizedSearchCV(estimator=linear_svc, param_distributions = param_grid, scoring='accuracy', n_jobs = -1, cv = 3)
linear_clf.fit(X_train_red, y_train.values.ravel())
linear_gamma = linear_clf.best_params_['gamma']
linear_C = linear_clf.best_params_['C']
print((linear_C, linear_gamma))

lin_svm = SVC(kernel = 'linear', C = 3, gamma = 0.2, random_state = 42).fit(X_train_red, y_train.values.ravel())

print(model_info(lin_svm, X_train_red, y_train.values.ravel(), "lin_svm", "train"))
print(model_info(lin_svm, X_test_red, y_test, "lin_svm", "test"))

"""Radial SVC"""

rbf_clf = RandomizedSearchCV(estimator=rbf_svc, param_distributions = param_grid, scoring='accuracy', n_jobs = -1, cv = 3)
rbf_clf.fit(X_train_red, y_train.values.ravel())
rbf_gamma = rbf_clf.best_params_['gamma']
rbf_C = rbf_clf.best_params_['C']
print((rbf_C, rbf_gamma))

rbf_svm = SVC(C = 2.75, gamma = 0.2, random_state = 42, kernel = 'rbf').fit(X_train_red, y_train.values.ravel())

print(model_info(rbf_svm, X_train_red, y_train.values.ravel(), "rbf_svm", "train"))
print(model_info(rbf_svm, X_test_red, y_test, "rbf_svm", "test"))

"""Poly SVC"""

poly_clf = RandomizedSearchCV(estimator=poly_svc, param_distributions = poly_param_grid, scoring='accuracy', n_jobs = -1, cv = 3)
poly_clf.fit(X_train_red, y_train.values.ravel())
poly_deg = poly_clf.best_params_['degree']
print(poly_deg)

poly_svm = SVC(C = 2.75, gamma = 0.2, random_state = 42, kernel = 'poly', degree = 3).fit(X_train_red, y_train.values.ravel())

print(model_info(poly_svm, X_train_red, y_train.values.ravel(), "poly_svm", "train"))
print(model_info(poly_svm, X_test_red, y_test, "poly_svm", "test"))