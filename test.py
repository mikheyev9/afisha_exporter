from selenium import webdriver

url = 'https://stepik.org/a/104774'
browser = webdriver.Chrome(executable_path=r'chromedriver.exe')
browser.get(url)