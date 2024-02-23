from bs4 import BeautifulSoup
import datetime
import subprocess
import time
import os

def extract_links(file_path, class_name):
    # Open and read the .snapshot file
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')

    links = []

    for link in soup.find_all('a', class_ = class_name):
        href = link.get('href')
        if href:
            links.append(href)
    return links


# get time range
def get_time(file_path):
    file_name = file_path.split('/')[-1]
    time_str = file_name.split('.')[0]

    return time_str


# convert string date time to unix timestamp
def convert_to_unix(date_time_str):
    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y%m%d%H%M%S')
    timestamp = str(int(date_time_obj.timestamp()))
    return timestamp


if __name__ == '__main__':
    # Path to your .snapshot files
    dir_path = 'www.nytimes.com'
    file_ls = []
    for (dir_path, dir_names, file_names) in os.walk(dir_path):
        # file_path = 'nytimes/20240128031617.snapshot'
        for file_name in file_names:
            if file_name.endswith('.snapshot') and file_name not in file_ls:
                file_ls.append(file_name)
        
        # # don't look inside any subdirectory
        # break
    print(file_ls)
    
    for file_name in file_ls[1:]:
        file_path = os.path.join(dir_path, file_name)
        # extract links from the .snapshot file
        links = extract_links(file_path, 'css-9mylee')
        time = get_time(file_path)

        for link in links:
            # get the file name without prefix
            link = link.split('www.')[-1]
            shell_command = 'wayback-machine-scraper -f ' + time + ' -t ' + time + ' -a "' + link + '$" ' + link
            subprocess.Popen(shell_command, shell=True)