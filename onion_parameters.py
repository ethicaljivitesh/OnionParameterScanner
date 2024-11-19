#!/usr/bin/env python3

import os
import sys
import threading
import queue
import requests
from requests.exceptions import RequestException
from colorama import Fore, Style, init
import logging
import time


init(autoreset=True)


TOR_PROXY = "socks5h://127.0.0.1:9050"  # Tor proxy address
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
]
TIMEOUT = 10  # Timeout for requests in seconds
THREAD_COUNT = 10  # Number of threads for enumeration
DEFAULT_WORDLIST = "common.txt"  # Default wordlist path
VERBOSE = False  # Verbose logging toggle

# Logging Configuration
logging.basicConfig(filename="parameter_scan.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Banner
def banner():
    print(f"""
{Fore.BLUE}==================================================
    .onion Parameter Enumerator
    Author: Jivitesh Khatri
    Advanced Features: Multi-threading, AI, Logging
==================================================
{Style.RESET_ALL}
""")

# Check Tor Connection
def check_tor_connection():
    try:
        print(f"{Fore.YELLOW}[*] Checking Tor connection...")
        response = requests.get(
            "http://check.torproject.org", proxies={"http": TOR_PROXY, "https": TOR_PROXY}, timeout=TIMEOUT
        )
        if "Congratulations. This browser is configured to use Tor." in response.text:
            print(f"{Fore.GREEN}[+] Tor is working correctly!")
        else:
            print(f"{Fore.RED}[-] Tor is not configured properly. Ensure Tor is running.")
            sys.exit(1)
    except RequestException as e:
        print(f"{Fore.RED}[-] Error connecting to Tor: {e}")
        sys.exit(1)

# Parameter Enumeration Worker
def param_enum_worker(target_url, word_queue, results, lock):
    while not word_queue.empty():
        param = word_queue.get()
        url = f"{target_url}?{param}=test"
        user_agent = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            response = requests.get(url, proxies={"http": TOR_PROXY, "https": TOR_PROXY}, headers=user_agent, timeout=TIMEOUT)
            with lock:
                if response.status_code == 200:
                    results.append((url, response.status_code, len(response.content)))
                    print(f"{Fore.GREEN}[+] Found: {url} [Status: {response.status_code}, Size: {len(response.content)}]")
                elif response.status_code in [301, 302]:
                    print(f"{Fore.YELLOW}[~] Redirect: {url} [Status: {response.status_code}]")
                else:
                    if VERBOSE:
                        print(f"{Fore.RED}[-] No success: {url} [Status: {response.status_code}]")
            logging.info(f"Checked: {url} [Status: {response.status_code}]")
        except RequestException as e:
            with lock:
                print(f"{Fore.RED}[-] Error accessing {url}: {e}")
            logging.error(f"Error accessing {url}: {e}")
        word_queue.task_done()

# Load Wordlist
def load_wordlist(wordlist_path):
    if not os.path.exists(wordlist_path):
        print(f"{Fore.RED}[-] Wordlist not found: {wordlist_path}")
        sys.exit(1)
    with open(wordlist_path, "r") as file:
        params = [line.strip() for line in file if line.strip()]
    print(f"{Fore.GREEN}[+] Loaded {len(params)} parameters from wordlist.")
    return params

# Main Function
def main():
    global VERBOSE
    banner()

    # Ensure Tor is running
    check_tor_connection()

    # Input target .onion URL
    target_url = input("[*] Enter .onion URL (e.g., http://exampleonion.onion): ").strip()
    if not target_url.endswith(".onion"):
        print(f"{Fore.RED}[-] Invalid .onion URL. Make sure it ends with .onion.")
        sys.exit(1)

    # Enable Verbose Mode
    verbose_input = input("[*] Enable verbose mode? (y/n, default n): ").strip().lower()
    VERBOSE = verbose_input == "y"

    # Load wordlist
    wordlist_path = input("[*] Enter path to wordlist (default: common.txt): ").strip() or DEFAULT_WORDLIST
    params = load_wordlist(wordlist_path)

    # Create a queue for parameters
    word_queue = queue.Queue()
    for param in params:
        word_queue.put(param)

    # Start timer
    start_time = time.time()

    # Parameter Enumeration
    print(f"{Fore.BLUE}[*] Starting parameter enumeration...")
    results = []
    lock = threading.Lock()
    threads = []

    for _ in range(THREAD_COUNT):
        thread = threading.Thread(target=param_enum_worker, args=(target_url, word_queue, results, lock))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Save results to file
    output_file = input("[*] Enter output file name (default: enumeration_results.txt): ").strip() or "enumeration_results.txt"
    with open(output_file, "w") as file:
        for url, status, size in results:
            file.write(f"{url} [Status: {status}, Size: {size}]\n")

    elapsed_time = time.time() - start_time
    print(f"{Fore.GREEN}[+] Enumeration complete in {elapsed_time:.2f} seconds.")
    print(f"{Fore.GREEN}[+] Results saved to {output_file}.")

if __name__ == "__main__":
    main()
