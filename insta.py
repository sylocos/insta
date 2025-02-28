import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Proxy listelerini almak için birden fazla kaynağı kullanma
def get_free_proxies():
    proxy_sources = [
        "https://www.sslproxies.org/",  # SSLProxies
        "https://free-proxy-list.net/",  # Free Proxy List
        "https://www.spys.one/en/",  # Spys One
        "https://www.proxyscrape.com/",  # Proxy Scrape
    ]
    
    proxies = []
    for url in proxy_sources:
        try:
            response = requests.get(url)
            proxies.extend(parse_proxy_list(response.text))
        except Exception as e:
            logging.error(f"{url} adresinden proxy listesi alınırken hata oluştu: {e}")
    return proxies

# Proxy listesi parse etme
def parse_proxy_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    proxies = []
    table = soup.find('table')  # Adjust according to the website's HTML structure
    for row in table.find_all('tr')[1:]:
        tds = row.find_all('td')
        try:
            ip = tds[0].text.strip()
            port = tds[1].text.strip()
            proxy = f"{ip}:{port}"
            proxies.append(proxy)
        except IndexError:
            continue
    return proxies

# Proxy'yi Selenium'da kullanmak
def set_up_proxy(proxy):
    options = Options()
    options.add_argument(f'--proxy-server={proxy}')
    options.add_argument("--incognito")  # Gizli mod
    driver = webdriver.Chrome(options=options)
    return driver

# Proxy Doğrulama (geçerli proxy'leri filtreleme)
def validate_proxy(proxy):
    test_url = "http://httpbin.org/ip"
    try:
        response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

# Proxy doğrulama ve geçerli proxy'leri seçme
def get_valid_proxies(proxies):
    valid_proxies = [proxy for proxy in proxies if validate_proxy(proxy)]
    logging.info(f"Geçerli Proxy'ler: {valid_proxies}")
    return valid_proxies

# Instagram Hesap Açma Fonksiyonu
def create_instagram_account(driver, email, username, full_name, password):
    try:
        driver.get("https://www.instagram.com/accounts/emailsignup/")

        # Formun yüklenmesini bekleyin
        time.sleep(3)

        # E-posta, kullanıcı adı, isim ve şifreyi gir
        email_input = driver.find_element(By.NAME, "emailOrPhone")
        email_input.send_keys(email)
        
        full_name_input = driver.find_element(By.NAME, "fullName")
        full_name_input.send_keys(full_name)
        
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys(username)
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        # Formu gönder
        password_input.send_keys(Keys.RETURN)
        time.sleep(5)  # Sayfanın yüklenmesini bekleyin

        logging.info(f"{username} hesabı başarıyla oluşturuldu.")
    except Exception as e:
        logging.error(f"{username} hesabı oluşturulurken hata oluştu: {e}")

# Temp-Mail API ile E-posta Alımı
def get_temp_mail():
    temp_mail_url = "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1"
    try:
        response = requests.get(temp_mail_url)
        email = response.json()[0]
        return email
    except Exception as e:
        logging.error(f"Geçici e-posta alınırken hata oluştu: {e}")
        return None

# CAPTCHA çözümü için 2Captcha API
def solve_captcha(api_key, site_key, page_url):
    try:
        captcha_request_url = f"https://2captcha.com/in.php?key={api_key}&method=userrecaptcha&googlekey={site_key}&pageurl={page_url}"
        response = requests.get(captcha_request_url)
        captcha_id = response.text.split('|')[1]
        
        # CAPTCHA çözülene kadar bekleyin
        time.sleep(20)

        # CAPTCHA sonucunu alın
        solution_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}"
        solution_response = requests.get(solution_url)
        while 'CAPCHA_NOT_READY' in solution_response.text:
            time.sleep(5)
            solution_response = requests.get(solution_url)
        return solution_response.text.split('|')[1]
    except Exception as e:
        logging.error(f"CAPTCHA çözülürken hata oluştu: {e}")
        return None

# Profil Resmi İndirme
def download_random_profile_picture():
    image_url = "https://picsum.photos/200"  # Örnek rastgele görsel URL'si
    img_data = requests.get(image_url).content
    filename = f"profile_pic_{random.randint(1, 10000)}.jpg"
    with open(filename, 'wb') as f:
        f.write(img_data)
    logging.info(f"Profil resmi indirildi: {filename}")
    return filename

# Hesapta Profil Resmi Yükleme
def upload_profile_picture(driver, image_path):
    driver.get("https://www.instagram.com/accounts/edit/")
    time.sleep(2)
    
    # Profil fotoğrafını yüklemek için butonu tıklayın
    profile_picture_input = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Change profile picture")]')
    profile_picture_input.click()
    time.sleep(2)
    
    # Dosya seçme ve yükleme işlemi
    upload_input = driver.find_element(By.XPATH, '//*[contains(@type, "file")]')
    upload_input.send_keys(os.path.abspath(image_path))
    time.sleep(2)

# Gönderi Paylaşma
def share_post(driver, image_path, caption):
    driver.get("https://www.instagram.com/create/style/")
    time.sleep(3)

    # Görsel yükleme
    upload_input = driver.find_element(By.XPATH, '//*[contains(@type, "file")]')
    upload_input.send_keys(os.path.abspath(image_path))
    time.sleep(2)

    # Açıklama girme
    caption_input = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Write a caption...")]')
    caption_input.send_keys(caption)
    time.sleep(2)

    # Paylaş butonuna tıklama
    share_button = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Share")]')
    share_button.click()
    time.sleep(5)

# Kullanıcıyı Takip Etme
def follow_user(driver, user_to_follow):
    try:
        driver.get(f"https://www.instagram.com/{user_to_follow}/")
        time.sleep(3)
        follow_button = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Follow")]')
        follow_button.click()
        logging.info(f"{user_to_follow} kullanıcısı takip edildi.")
    except Exception as e:
        logging.error(f"{user_to_follow} kullanıcısı takip edilirken hata oluştu: {e}")

# Kullanıcı Adı ve Şifreyi Txt Dosyasına Kaydetme
def save_account_info(username, password):
    with open("account_credentials.txt", "a") as f:
        f.write(f"{username}:{password}\n")
    logging.info(f"Hesap bilgileri kaydedildi: {username}:{password}")

# Proxy, E-posta ve CAPTCHA işlemleriyle hesap oluşturun
def create_multiple_accounts(num_accounts, user_to_follow):
    # Proxy kullanımı
    proxies = get_free_proxies()
    valid_proxies = get_valid_proxies(proxies)

    # Eğer geçerli proxy yoksa, işlemi sonlandır
    if not valid_proxies:
        logging.error("Geçerli proxy bulunamadı, işlem sonlandırılıyor.")
        return

    # Her hesap için döngü
    for i in range(num_accounts):
        proxy = random.choice(valid_proxies)
        logging.info(f"{i+1}. Proxy: {proxy}")

        # Selenium ile tarayıcıyı başlat
        driver = set_up_proxy(proxy)

        # E-posta, kullanıcı adı ve şifre oluşturma
        temp_mail = get_temp_mail()
        if temp_mail is None:
            logging.error("Geçici e-posta alınamadı, yeni hesap oluşturulacak.")
            driver.quit()
            continue
        logging.info(f"Geçici E-posta: {temp_mail}")

        username = f"user_{random.randint(10000, 99999)}"
        password = f"StrongPassword{random.randint(1000, 9999)}!"
        full_name = f"User {random.randint(1, 100)}"

        # Hesap oluşturma
        create_instagram_account(driver, temp_mail, username, full_name, password)

        # CAPTCHA çözülmesi gerekiyorsa, bunu çöz
        api_key = "013d829512a5845136d8557f6752743d"
        site_key = "6Lc_12345678"  # Instagram'ın CAPTCHA site key'i
        page_url = "https://www.instagram.com/accounts/emailsignup/"
        captcha_solution = solve_captcha(api_key, site_key, page_url)
        if captcha_solution:
            logging.info(f"CAPTCHA Çözümü: {captcha_solution}")

        # Profil resmi indir ve yükle
        profile_picture = download_random_profile_picture()
        upload_profile_picture(driver, profile_picture)

        # Aynı görseli paylaş
        caption = "Rastgele profil resmi ile ilk gönderi!"
        share_post(driver, profile_picture, caption)

        # Belirtilen kullanıcıyı takip et
        follow_user(driver, user_to_follow)

        # Hesap bilgilerini kaydet
        save_account_info(username, password)

        # Tarayıcıyı kapat
        driver.quit()

        # Hesap oluşturma arasına rastgele bir bekleme süresi ekleyin
        time.sleep(random.randint(10, 30))  # 10-30 saniye arasında rastgele bekleyin

# Ana fonksiyon: 1000 hesap oluşturma
if __name__ == "__main__":
    num_accounts = 1000  # 1000 hesap oluşturuyoruz
    user_to_follow = "specific_user"  # Takip edilecek kullanıcı adı
    create_multiple_accounts(num_accounts, user_to_follow)