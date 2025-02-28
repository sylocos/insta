import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sabit proxy listesi
def get_free_proxies():
    # Elle girilmiş örnek proxy listesi - bu listeyi güncel proxy'lerle değiştirmeniz gerekir
    proxy_list = [
        "103.155.54.233:83",
        "103.48.68.107:83", 
        "154.85.58.149:80",
        "185.15.172.212:3128",
        "185.199.229.156:7492",
        "185.199.228.220:7300",
        "185.199.231.45:8382",
        "188.74.210.207:6286",
        "188.74.183.10:8279",
        "188.74.210.21:6100",
        "45.155.68.129:8133",
        "154.85.58.149:80",
        "185.15.172.212:3128",
        "45.155.68.129:8133",
        "103.48.68.107:82",
        "146.59.199.12:80",
        "51.79.50.22:9300",
        "51.79.50.31:9300"
    ]
    return proxy_list

# Proxy'yi Selenium'da kullanmak
def set_up_proxy(proxy):
    options = Options()
    options.add_argument(f'--proxy-server={proxy}')
    options.add_argument("--incognito")  # Gizli mod
    options.add_argument('--headless')  # Tarayıcıyı görünmez modda çalıştır
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return driver

# Proxy Doğrulama (geçerli proxy'leri filtreleme)
def validate_proxy(proxy):
    test_url = "http://httpbin.org/ip"
    try:
        response = requests.get(test_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

# Proxy doğrulama ve geçerli proxy'leri seçme
def get_valid_proxies(proxies):
    valid_proxies = []
    for proxy in proxies:
        if validate_proxy(proxy):
            valid_proxies.append(proxy)
            logging.info(f"Geçerli proxy bulundu: {proxy}")
    if not valid_proxies:
        logging.warning("Hiç geçerli proxy bulunamadı!")
    return valid_proxies

# Instagram Hesap Açma Fonksiyonu
def create_instagram_account(driver, email, username, full_name, password):
    try:
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(random.uniform(3, 5))  # Rastgele bekleme süresi

        # E-posta, kullanıcı adı, isim ve şifreyi gir
        email_input = driver.find_element(By.NAME, "emailOrPhone")
        email_input.send_keys(email)
        time.sleep(random.uniform(1, 2))
        
        full_name_input = driver.find_element(By.NAME, "fullName")
        full_name_input.send_keys(full_name)
        time.sleep(random.uniform(1, 2))
        
        username_input = driver.find_element(By.NAME, "username")
        username_input.send_keys(username)
        time.sleep(random.uniform(1, 2))
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(random.uniform(2, 3))

        # Formu gönder
        password_input.send_keys(Keys.RETURN)
        time.sleep(random.uniform(5, 7))

        logging.info(f"{username} hesabı başarıyla oluşturuldu.")
    except Exception as e:
        logging.error(f"{username} hesabı oluşturulurken hata oluştu: {e}")
        raise

# Temp-Mail API ile E-posta Alımı
def get_temp_mail():
    temp_mail_urls = [
        "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1",
        "https://api.temp-mail.org/request/mail/generate",
        "https://10minutemail.net/address.api.php"
    ]
    
    for url in temp_mail_urls:
        try:
            response = requests.get(url)
            if url.endswith("count=1"):
                email = response.json()[0]
            else:
                email = response.json().get("email")
            if email:
                return email
        except Exception as e:
            logging.warning(f"Temp mail servisi {url} ile hata: {e}")
            continue
    
    # Hiçbir servis çalışmazsa rastgele mail oluştur
    random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
    return f"{random_string}@temporary.com"

# CAPTCHA çözümü için 2Captcha API
def solve_captcha(api_key, site_key, page_url):
    try:
        captcha_request_url = f"https://2captcha.com/in.php?key={api_key}&method=userrecaptcha&googlekey={site_key}&pageurl={page_url}"
        response = requests.get(captcha_request_url)
        if "ERROR" in response.text:
            logging.error(f"CAPTCHA isteği başarısız: {response.text}")
            return None
            
        captcha_id = response.text.split('|')[1]
        logging.info(f"CAPTCHA ID alındı: {captcha_id}")
        
        # CAPTCHA çözülene kadar bekleyin
        max_attempts = 24  # 2 dakika (5 saniye * 24)
        for attempt in range(max_attempts):
            time.sleep(5)
            solution_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}"
            solution_response = requests.get(solution_url)
            
            if "OK|" in solution_response.text:
                solution = solution_response.text.split('|')[1]
                logging.info("CAPTCHA çözümü başarılı")
                return solution
                
        logging.error("CAPTCHA çözümü zaman aşımına uğradı")
        return None
    except Exception as e:
        logging.error(f"CAPTCHA çözümü sırasında hata: {e}")
        return None

# Ana fonksiyon: Hesap oluşturma
def create_multiple_accounts(num_accounts, user_to_follow):
    # Proxy kullanımı
    proxies = get_free_proxies()
    valid_proxies = get_valid_proxies(proxies)

    if not valid_proxies:
        logging.error("Hiç geçerli proxy bulunamadı! Program sonlandırılıyor.")
        return

    successful_accounts = 0
    for i in range(num_accounts):
        try:
            proxy = random.choice(valid_proxies)
            logging.info(f"Hesap {i+1}/{num_accounts} için proxy: {proxy}")

            # Selenium ile tarayıcıyı başlat
            driver = set_up_proxy(proxy)

            try:
                # Hesap bilgilerini oluştur
                temp_mail = get_temp_mail()
                if not temp_mail:
                    raise Exception("Geçici e-posta alınamadı")

                username = f"user_{random.randint(10000, 99999)}"
                password = f"StrongPassword{random.randint(1000, 9999)}!"
                full_name = f"User {random.randint(1, 100)}"

                # Hesap oluştur
                create_instagram_account(driver, temp_mail, username, full_name, password)
                
                # Hesap bilgilerini kaydet
                save_account_info(username, password)
                
                successful_accounts += 1
                logging.info(f"Başarılı hesap sayısı: {successful_accounts}")

            except Exception as e:
                logging.error(f"Hesap oluşturma hatası: {e}")
            finally:
                driver.quit()

            # Hesaplar arası rastgele bekleme
            wait_time = random.randint(30, 60)
            logging.info(f"Sonraki hesap için {wait_time} saniye bekleniyor...")
            time.sleep(wait_time)

        except Exception as e:
            logging.error(f"Genel hata: {e}")
            continue

    logging.info(f"İşlem tamamlandı. Toplam başarılı hesap: {successful_accounts}/{num_accounts}")

# Kullanıcı Adı ve Şifreyi Txt Dosyasına Kaydetme
def save_account_info(username, password):
    try:
        with open("account_credentials.txt", "a") as f:
            f.write(f"{username}:{password}\n")
        logging.info(f"Hesap bilgileri kaydedildi: {username}")
    except Exception as e:
        logging.error(f"Hesap bilgileri kaydedilirken hata: {e}")

if __name__ == "__main__":
    try:
        num_accounts = 5  # Başlangıç için daha az sayıda hesap
        user_to_follow = "specific_user"
        logging.info("Program başlatılıyor...")
        create_multiple_accounts(num_accounts, user_to_follow)
    except KeyboardInterrupt:
        logging.info("Program kullanıcı tarafından sonlandırıldı.")
    except Exception as e:
        logging.error(f"Program beklenmeyen bir hatayla sonlandı: {e}")