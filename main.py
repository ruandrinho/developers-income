import requests
import os
from itertools import count
from terminaltables import AsciiTable
from tqdm import tqdm
from dotenv import load_dotenv


def predict_salary_by_interval(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def predict_rub_salary_sj(vacancy):
    return predict_salary_by_interval(vacancy['payment_from'],
                                      vacancy['payment_to'])


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']['currency'] != 'RUR':
        return
    return predict_salary_by_interval(vacancy['salary']['from'],
                                      vacancy['salary']['to'])


def format_vacancies_as_table(vacancies, title):
    table_data = [
        ['Язык', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for language, statistics in vacancies.items():
        table_data.append([
            language,
            statistics['vacancies_found'],
            statistics['vacancies_processed'],
            statistics['average_salary']
        ])
    return AsciiTable(table_data, title).table


def get_vacancies_statistics_sj(api_url, params, headers):
    salaries = []
    vacancies_found, vacancies_processed, average_salary = 0, 0, 0
    for page in tqdm(count(0), desc='Pages', position=1, leave=False):
        params['page'] = page
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_with_meta = response.json()
        if not vacancies_with_meta['more']:
            break
        for vacancy in vacancies_with_meta['objects']:
            vacancies_found += 1
            predicted_salary = predict_rub_salary_sj(vacancy)
            if predicted_salary:
                salaries.append(predicted_salary)
    if vacancies_found:
        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries) / len(salaries))
    return vacancies_found, vacancies_processed, average_salary


def find_vacancies_sj(languages, superjob_secret_key):
    vacancies_statistics = {}
    api_url = 'https://api.superjob.ru/2.0/vacancies/'
    params = {
        'town': 4  # id Москвы в API SuperJob
    }
    headers = {
        'X-Api-App-Id': superjob_secret_key
    }
    for language in tqdm(languages, desc='Languages', position=0):
        params['keyword'] = f'Программист {language}'
        vacancies_found, vacancies_processed, average_salary =\
            get_vacancies_statistics_sj(api_url, params, headers)
        vacancies_statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return vacancies_statistics


def get_vacancies_statistics_hh(api_url, params, headers):
    salaries = []
    vacancies_found, vacancies_processed, average_salary = 0, 0, 0
    for page in tqdm(count(0), desc='Pages', position=1, leave=False):
        params['page'] = page
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_with_meta = response.json()
        if page >= vacancies_with_meta['pages']:
            break
        for vacancy in vacancies_with_meta['items']:
            vacancies_found += 1
            predicted_salary = predict_rub_salary_hh(vacancy)
            if predicted_salary:
                salaries.append(predicted_salary)
    if vacancies_found:
        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries) / len(salaries))
    return vacancies_found, vacancies_processed, average_salary


def find_vacancies_hh(languages):
    vacancies_statistics = {}
    api_url = 'https://api.hh.ru/vacancies'
    params = {
        'area': 1,  # id Москвы в API HeadHunter
        'period': 30,
        'only_with_salary': True
    }
    headers = {
        'User-Agent': 'Developers-Income/1.0 (dvmn@dvmn.org)'
    }
    for language in tqdm(languages, desc='Languages', position=0):
        params['text'] = f'Программист {language}'
        vacancies_found, vacancies_processed, average_salary =\
            get_vacancies_statistics_hh(api_url, params, headers)
        vacancies_statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return vacancies_statistics


def main():
    load_dotenv()
    languages = ('Python', 'Java', 'JavaScript', 'C#', 'C++', 'PHP',
                 'Typescript', 'Swift', 'Go', 'Node.js')
    print('Fetching HeadHunter...')
    hh_vacancies = find_vacancies_hh(languages)
    print('Fetching Superjob...')
    superjob_vacancies = find_vacancies_sj(languages,
                                           os.getenv('SUPERJOB_SECRET_KEY'))
    print(format_vacancies_as_table(hh_vacancies, 'HeadHunter Moscow'))
    print()
    print(format_vacancies_as_table(superjob_vacancies, 'SuperJob Moscow'))


if __name__ == '__main__':
    main()
