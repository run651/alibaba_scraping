import requests
from bs4 import BeautifulSoup
from lxml import html
from playwright.sync_api import sync_playwright


def scrape_static(url, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
    print(f"\n[STATIC FETCH] {url}\n")
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.raise_for_status()
    html_content = res.text
    extract_content(html_content, tag, class_name, id_name, css_selector, xpath_selector)


def scrape_dynamic(url, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
    print(f"\n[DYNAMIC FETCH] {url}\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=600000)  # wait for page load
        page.wait_for_load_state("networkidle")  # wait until network is idle
        html_content = page.content()
        print(html_content)
        extract_content(html_content, tag, class_name, id_name, css_selector, xpath_selector)
        browser.close()


def extract_content(html_content, tag=None, class_name=None, id_name=None, css_selector=None, xpath_selector=None):
    # --- BeautifulSoup for tag/class/id/css ---
    soup = BeautifulSoup(html_content, "html.parser")

    if tag:
        elements = soup.find_all(tag)
        print(f"Results for tag <{tag}>:")
        for e in elements[:5]:
            print(" ", e.get_text(strip=True))

    if class_name:
        elements = soup.find_all(class_=class_name)
        print(f"\nResults for class='{class_name}':")
        for e in elements[:5]:
            print(" ", e.get_text(strip=True))

    if id_name:
        element = soup.find(id=id_name)
        print(f"\nResults for id='{id_name}':")
        if element:
            print(" ", element.get_text(strip=True))

    if css_selector:
        elements = soup.select(css_selector)
        print(f"\nResults for CSS selector '{css_selector}':")
        for e in elements[:5]:
            print(" ", e.get_text(strip=True))

    # --- lxml for XPath ---
    if xpath_selector:
        tree = html.fromstring(html_content)
        results = tree.xpath(xpath_selector)
        print(f"\nResults for XPath '{xpath_selector}':")
        for r in results[:5]:
            if hasattr(r, "text_content"):
                print(" ", r.text_content().strip())
            else:
                print(" ", str(r).strip())


# --- Example test run ---
if __name__ == "__main__":
    test_url = "https://example.com"  # change this to your target

    # Static test
    scrape_static(
        url=test_url,
        tag="h1",
        class_name="example",
        id_name="main",
        css_selector="p",
        xpath_selector="//h1/text()"
    )

    # Dynamic test
    scrape_dynamic(
        url=test_url,
        tag="h1",
        class_name="example",
        id_name="main",
        css_selector="p",
        xpath_selector="//h1/text()"
    )