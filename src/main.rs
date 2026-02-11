use scraper::{Html, Selector};
use std::env;

fn get_problem_urls(html: &str) -> Vec<String> {
    let document = Html::parse_document(&html);
    let selector = Selector::parse("td.text-center a").unwrap();

    document
        .select(&selector)
        .filter_map(|element| {
            let href = element.value().attr("href")?;
            if href.contains("/tasks/") {
                Some(format!("https://atcoder.jp{}", href))
            } else {
                None
            }
        })
        .collect()
}

fn get(contest_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    let contest_url = format!("https://atcoder.jp/contests/{}/tasks", contest_name);
    let body = reqwest::blocking::get(contest_url)?.text()?;
    let urls = get_problem_urls(&body);
    for x in urls {
        println!("{}", x);
    }
    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        println!("コンテスト名を入力してください");
        return;
    }
    get(&args[1]).expect("取得に失敗しました");
}
