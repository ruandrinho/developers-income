import requests
import os
from itertools import count
from terminaltables import AsciiTable
from tqdm import tqdm
from dotenv import load_dotenv


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']['currency'] != 'RUR':
        return
    return predict_salary(vacancy['salary']['from'],
                          vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def format_vacancies_as_table(vacancies, title):
    table_data = [
        ['Язык', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for language, vacancies_data in vacancies.items():
        table_data.append([
            language,
            vacancies_data['vacancies_found'],
            vacancies_data['vacancies_processed'],
            vacancies_data['average_salary']
        ])
    return AsciiTable(table_data, title).table


def find_vacancies_sj(languages):
    vacancies = {}
    api_url = 'https://api.superjob.ru/2.0/vacancies/'
    params = {
        'keyword': 'Программист',
        'town': 4
    }
    headers = {
        'Host': 'api.superjob.ru',
        'X-Api-App-Id': os.getenv('SUPERJOB_SECRET_KEY')
    }
    for language in tqdm(languages, desc='Languages', position=0):
        salaries = []
        vacancies[language] = {
            'vacancies_found': 0,
            'vacancies_processed': 0,
            'average_salary': 0
        }
        params['keyword'] = f'Программист {language}'
        for page in tqdm(count(0), desc='Pages', position=1, leave=False):
            params['page'] = page
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            page_data = response.json()
            if not page_data['more']:
                break
            for item in page_data['objects']:
                vacancies[language]['vacancies_found'] += 1
                predicted_salary = predict_rub_salary_sj(item)
                if predicted_salary:
                    salaries.append(predicted_salary)
        if vacancies[language]['vacancies_found']:
            vacancies[language]['vacancies_processed'] = len(salaries)
            vacancies[language]['average_salary'] =\
                int(sum(salaries) / len(salaries))
    return vacancies


def find_vacancies_hh(languages):
    vacancies = {}
    api_url = 'https://api.hh.ru/vacancies'
    params = {
        'text': 'Программист',
        'area': 1,
        'period': 30,
        'only_with_salary': True
    }
    headers = {
        'User-Agent': 'Developers-Income/1.0 (dvmn@dvmn.org)'
    }
    for language in tqdm(languages, desc='Languages', position=0):
        salaries = []
        vacancies[language] = {
            'vacancies_found': 0,
            'vacancies_processed': 0,
            'average_salary': 0
        }
        params['text'] = f'Программист {language}'
        for page in tqdm(count(0), desc='Pages', position=1, leave=False):
            params['page'] = page
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            page_data = response.json()
            if page >= page_data['pages']:
                break
            for item in page_data['items']:
                vacancies[language]['vacancies_found'] += 1
                predicted_salary = predict_rub_salary_hh(item)
                if predicted_salary:
                    salaries.append(predicted_salary)
        if vacancies[language]['vacancies_found']:
            vacancies[language]['vacancies_processed'] = len(salaries)
            vacancies[language]['average_salary'] =\
                int(sum(salaries) / len(salaries))
    return vacancies


def main():
    load_dotenv()
    languages = ('Python', 'Java', 'JavaScript', 'C#', 'C++', 'PHP',
                 'Typescript', 'Swift', 'Go', 'Node.js')
    print('Fetching HeadHunter...')
    hh_vacancies = find_vacancies_hh(languages)
    print('Fetching Superjob...')
    superjob_vacancies = find_vacancies_sj(languages)
    print(format_vacancies_as_table(hh_vacancies, 'HeadHunter Moscow'))
    print(format_vacancies_as_table(superjob_vacancies, 'SuperJob Moscow'))


if __name__ == '__main__':
    main()
