use scraper::{Html, Selector};
use std::env;

fn get_sample_case(url: &str) -> Result<(), Box<dyn std::error::Error>> {
    let body = reqwest::blocking::get(url)?.text()?;
    let document = Html::parse_document(&body);

    let selector_section = Selector::parse(".part").unwrap();
    let selector_h3 = Selector::parse("h3").unwrap();
    let selector_pre = Selector::parse("pre").unwrap();

    let cases: Vec<String> = document
        .select(&selector_section)
        .filter_map(|section| {
            let h3_text = section
                .select(&selector_h3)
                .next()?
                .text()
                .collect::<String>();

            if h3_text.contains("入力例") {
                let pre_text = section
                    .select(&selector_pre)
                    .next()?
                    .text()
                    .collect::<String>();
                Some(format!("{}\n{}", h3_text, pre_text))
            } else {
                None
            }
        })
        .collect();
    for x in cases {
        println!("{}", x);
    }
    Ok(())
}

fn get_problem_urls(contest_name: &str) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let contest_url = format!("https://atcoder.jp/contests/{}/tasks", contest_name);
    // コンテストの問題一覧ページの HTML を取得
    let html = reqwest::blocking::get(contest_url)?.text()?;

    let document = Html::parse_document(&html);
    // URL が書かれている a タグの class を指定
    let selector = Selector::parse("td.text-center a").unwrap();

    let urls: Vec<String> = document
        .select(&selector)
        .filter_map(|element| {
            let href = element.value().attr("href")?;
            if href.contains("/tasks/") {
                Some(format!("https://atcoder.jp{}", href))
            } else {
                None
            }
        })
        .collect::<Vec<String>>();

    Ok(urls)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        println!("コンテスト名を入力してください");
        return Ok(());
    }
    let urls: Vec<String> = get_problem_urls(&args[1])?;
    for x in &urls {
        println!("{}", x);
        get_sample_case(&x).expect("サンプルケースの取得に失敗しました");
    }
    Ok(())
}
