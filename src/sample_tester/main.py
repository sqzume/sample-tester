#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from colorama import Fore, init
from dotenv import load_dotenv

init(autoreset=True)

dotenv_path = Path.home() / ".config" / "st"
if not dotenv_path.exists():
    dotenv_path.mkdir()
load_dotenv(dotenv_path=f"{dotenv_path}/.env", verbose=True)
revel_session = os.getenv("REVEL_SESSION")
if revel_session is None:
    print("REVEL_SESSION を .env に指定してください")
    sys.exit(1)
session = requests.Session()
session.cookies.set("REVEL_SESSION", revel_session, domain="atcoder.jp")


def main():
    if len(sys.argv) == 1 or 3 < len(sys.argv):
        print("無効な引数です")
        sys.exit(1)

    contest = ""
    problem = ""
    source_file = ""
    if len(sys.argv) == 2:
        contest = check_config_file()
        problem = sys.argv[1]
        source_file = sys.argv[1]
    if len(sys.argv) == 3:
        contest = sys.argv[1]
        problem = sys.argv[2]
        source_file = "a"

    cache_path = Path.home() / ".cache" / "st"
    if not cache_path.exists():
        cache_path.mkdir()

    contest_path = Path.home() / ".cache" / "st" / f"{contest}"
    if not contest_path.exists():
        make_cache(contest)

    cases_in, cases_out = read_cache_case(contest, problem)

    # コンパイル
    path = Path(f"src/{source_file}.cpp")
    if not path.exists():
        print("ソースファイルが存在しません")
        sys.exit(1)
    print("コンパイルしています")
    compile(source_file)
    print("コンパイルが終わりました")

    # a.out が存在するかの確認
    path = Path("a.out")
    if not path.exists():
        print("a.out が存在しません")
        sys.exit(1)

    # a.out をサンプルケースを標準入力として実行
    cmd = ["./a.out"]
    n = len(cases_in)
    for i in range(n):
        input_data = cases_in[i]
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
        )
        print("---標準出力---")
        print(result.stdout.strip())
        print("---正解---")
        print(cases_out[i].strip())
        if result.stdout.split() == cases_out[i].split():
            print(Fore.GREEN + "AC")
        else:
            print(Fore.RED + "WA")


def make_cache(contest):
    cache_path = Path.home() / ".cache" / "st"
    if not cache_path.exists():
        cache_path.mkdir()
    contest_path = Path.home() / ".cache" / "st" / f"{contest}"
    if not contest_path.exists():
        contest_path.mkdir()

    problem_list = get_problems_list(contest)
    problem_list = list(dict.fromkeys(problem_list))
    for i in range(len(problem_list)):
        cases_in, cases_out = get_sample_case(contest, problem_list[i])
        problem_path = (
            Path.home() / ".cache" / "st" / f"{contest}" / f"{problem_list[i]}"
        )
        problem_path.mkdir()
        for j in range(len(cases_in)):
            case_in_path = (
                Path.home()
                / ".cache"
                / "st"
                / f"{contest}"
                / f"{problem_list[i]}"
                / f"case_{j + 1}.in"
            )
            case_out_path = (
                Path.home()
                / ".cache"
                / "st"
                / f"{contest}"
                / f"{problem_list[i]}"
                / f"case_{j + 1}.out"
            )
            with open(case_in_path, "w", encoding="utf-8") as f:
                f.write(cases_in[j])
            with open(case_out_path, "w", encoding="utf-8") as f:
                f.write(cases_out[j])
        time.sleep(0.5)


def read_cache_case(contest, problem):
    path = Path.home() / ".cache" / "st" / f"{contest}" / f"{problem}"
    if not path.exists():
        print("cache にファイルがありませんでした")
        sys.exit(1)
    file_count = sum(1 for p in path.iterdir() if p.is_file())
    file_count //= 2
    case_in = []
    case_out = []
    for i in range(file_count):
        infile_path = (
            Path.home()
            / ".cache"
            / "st"
            / f"{contest}"
            / f"{problem}"
            / f"case_{i + 1}.in"
        )
        outfile_path = (
            Path.home()
            / ".cache"
            / "st"
            / f"{contest}"
            / f"{problem}"
            / f"case_{i + 1}.out"
        )
        with open(infile_path, "r", encoding="utf-8") as f:
            case_in.append(f.read())
        with open(outfile_path, "r", encoding="utf-8") as f:
            case_out.append(f.read())
    return case_in, case_out


def check_config_file():
    path = Path("st.conf")
    if not path.exists():
        path.touch()
    with open("st.conf", "r", encoding="utf-8") as f:
        content = f.read()
        if content.split() == "":
            print("コンテスト名を指定してください")
            sys.exit(1)
        return content.strip()


def compile(file_name):
    cmd = ["g++", "-std=c++23", f"src/{file_name}.cpp"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("コンパイル時にエラーが発生しました")
        print(result.stderr)
        sys.exit(1)


def get_problems_list(contest):
    url = f"https://atcoder.jp/contests/{contest}/tasks"
    response = session.get(url)
    if response.status_code == 404:
        print("無効なコンテスト名です")
        sys.exit(1)
    if response.status_code != 200:
        print(f"問題一覧の取得に失敗しました ({response.status_code})")
        sys.exit(1)

    html_content = response.text
    document = BeautifulSoup(html_content, "html.parser")
    problem_urls = document.select("td.text-center a")

    problem_list = []
    for i in problem_urls:
        t = i.get("href")
        if t is None:
            print("リンクが見つかりませんでした")
            sys.exit(1)
        problem_list.append(str(t).split("_")[-1])
    return problem_list


def get_sample_case(contest, problem):
    url = f"https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem}"
    response = session.get(url)
    if response.status_code == 404:
        print("無効な URL です")
        sys.exit(1)
    if response.status_code != 200:
        print(f"問題ページの取得に失敗しました ({response.status_code})")
        sys.exit(1)

    html_content = response.text
    document = BeautifulSoup(html_content, "html.parser")
    sample_cases = document.select(".lang-ja div.part")

    cases_in = []
    cases_out = []
    for i in sample_cases:
        t = i.select_one("h3")
        if t is None:
            print("h3 が見つかりませんでした")
            sys.exit(1)

        s = t.text
        if s.startswith("入力例") or s.startswith("出力例"):
            x = i.select_one("pre")
            if x is None:
                print("pre が見つかりませんでした")
                sys.exit(1)

            case_text = x.text
            if s.startswith("入力例"):
                cases_in.append(case_text)
            if s.startswith("出力例"):
                cases_out.append(case_text)
    return cases_in, cases_out


if __name__ == "__main__":
    main()
