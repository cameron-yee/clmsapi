import requests
from glob import glob
import json
import pprint
import re
import os
import argparse
import auth
from collections import OrderedDict
from colors import bcolors

#CLI command definitions
def selectAction():
    parser = argparse.ArgumentParser(description='Pick action.')

    commands = {
        'uc': updateCoursePages,
    }
    
    parser.add_argument('command', help="Choose which function to run", choices=commands.keys())
    parser.add_argument('cid', help="Enter course ID", default="", type=str)
    parser.add_argument('top_directory', help="Enter the directory that contains the html files, or subfolders that contain the html files", type=str)

    args = parser.parse_args()
    return args


# def ucArgs():
#     parser = argparse.ArgumentParser(description='Arguments required for updateCoursePages()')
#     parser.add_argument('top_directory', help="Enter the directory that contains the html files, or subfolders that contain the html files", type=str)
#     uc_args = parser.parse_args()
#     return uc_args
    

#Returns list of sub direct subfolders from given directory
def getHtmlFolders(top_directory):
    final_directories = []
    raw_directories = [x for x in os.walk(top_directory)]
    processed_directories = raw_directories[0][1]
    for directory in processed_directories:
          final_directories.append('{}/{}'.format(top_directory, directory)) 
    return final_directories

#Returns a list of all html file paths in a given folder
def globHtml(directory):
    html_files = []
    html_files.append(glob(directory + '{}'.format('/**/*.html'), recursive=True))
    return html_files

    # sorted_dict = OrderedDict(sorted(html_dict.items(), key=lambda t: t[0]))
    # for dictionary in sorted_dict:
    #     print(dictionary)

    # print(sorted_dict)
    # return all_files


#Returns a dictionary of all course pages sorted alphabetically with html file path and html content as values
def storeHtmlData(html_files):
    html_data = getHtmlData(html_files)
    html_dict = {}
    sorted_dict = {}
    unset = []
    errors = False

    for i in range(len(html_files)):
        key = re.search('\d+_([^/]+.html$)', html_files[i])
        #sets the file 'url' without the 00_ as the key
        #stores both the full html file and the html data from the file
        if key:
            html_dict[str(key.group(1))] = html_files[i], html_data[i]
        else:
            unset.append(html_files[i])
            print(bcolors.FAIL + 'Unacceptable file names found.  Fix the following files: {}'.format(unset) + bcolors.ENDC)
            print(bcolors.WARNING + 'Make sure files follow the pattern: \'\\d+_([^/]+.html$)\'' + bcolors.ENDC)
            errors = True
        #sorts dictionary alphabetically by key
        sorted_dict = OrderedDict(sorted(html_dict.items(), key=lambda t: t[0]))

    # assert(errors == False)
    return sorted_dict


#Gets html body content for each page in course
def getHtmlData(html_files):
    html_data = []
    for html_file in html_files:
        if html_file is not None:
            with open(html_file, 'r') as f:
                contents = f.read()
                html_data.append(contents) 
                f.close()
    return html_data


def updateCoursePages(top_directory):
    html_files = []
    info_lists = []
    directories = getHtmlFolders(top_directory)

    #Glob html will work different if there are no sub folders
    if not directories:
        html_files = globHtml(top_directory)
        html_dict = storeHtmlData(html_files[0])
    else:
        for i in range(len(directories)):
            html_info = globHtml(directories[i])
            info_lists.append(html_info[0])
        list_of_files = [x for x in info_lists if x != []]
        for ls in list_of_files:
            for f in ls:
                html_files.append(f)
        html_dict = storeHtmlData(html_files)

    canvas_pages = getCoursePages(course_id, headers)
    urls = []
    for page_url in canvas_pages:
        urls.append(page_url)
        
    assert(len(urls) == len(html_dict))
    count = 0
    for key, values in html_dict.items():
        updateIndividualPage(course_id, headers, urls[count] , values[0], values[1]) 
        count += 1
    print(bcolors.BOLD + 'Success!' + bcolors.ENDC)
    

#Gets every page in a course and appends the page url to a list
def getCoursePages(course_id, headers):
    # page = 1
    count = 0
    pages = []
    isNext = True
    first = True
    url = url_base + course_id + '/pages?per_page=50&page=1&sort=title&order=asc'
    r = requests.get(url, headers=headers, timeout=20)

    try:
        while first:
            r = requests.get(r.links['current']['url'], headers=headers)
            # print(r.links['current']['url'])
            data = r.json()
            for page in data:
                pages.append(page['url'])
            first = False
        while isNext:
            r = requests.get(r.links['next']['url'], headers=headers)
            data = r.json()
            for page in data:
                pages.append(page['url'])
            count += 1
            # print(r.links['next']['url'])
    except KeyError:
        isNext = False

    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(pages)
    return pages


#DEPRECATED
#Updates html body content for each Canvas page in a given coures given the directory where the html files are stored
# def updateCoursePages(course_id, headers, html_files):
#     pages = getCoursePages(course_id, headers)
#     count = 0

#     assert(len(pages) == len(html_files))
#     for page_url in pages:
#         updateIndividualPage(course_id, headers, page_url, html_files[count])
#         count += 1


#Prints json object for individual page
def getPageInformation(course_id, page_url, headers):
    url = url_base + course_id + '/pages/' + page_url
    r = requests.get(url, headers=headers)
    r.json
    x = json.loads(r.text)
    print(json.dumps(x, sort_keys=True, indent=4))


#Updates html body content for given Canvas page and html file, for updating entire course
def updateIndividualPage(course_id, headers, page_url, file_name, html_content=None):
    if html_content is not None:
        url = url_base + course_id + '/pages/' + page_url
        data = [('wiki_page[body]', html_content),]
        r = requests.put(url, headers=headers, data=data)
        print(bcolors.OKBLUE + 'Updating: {}'.format(page_url) + bcolors.ENDC)
    else:
        url = url_base + course_id + '/pages/' + page_url
        with open(file_name, 'r') as f:
            html = f.read()
        data = [('wiki_page[body]', html),]
        r = requests.put(url, headers=headers, data=data)


#Create a new course in Canvas
def createNewCourse(course_name, headers):
    url = 'https://bscs.instructure.com/api/v1/accounts/1/courses'
    data = [('course[name]', course_name),]
    r = requests.post(url, headers=headers, data=data)


#Update course name
def updateCourseName(new_course_name, course_id, headers):
    url = url_base + course_id
    data = [('course[name]', new_course_name),]
    r = requests.put(url, headers=headers, data=data)


#Create a new module in a Canvas Course
def createNewModule(module_name, course_id, headers):
    url = url_base + course_id + '/modules'
    data = [('module[name]', module_name),]
    r = requests.post(url, headers=headers, data=data)


#Returns the id for the wanted module
def getModuleId(course_id, headers, module_name):
    url = url_base + course_id + '/modules'
    data = [('include[]', 'items'),]
    r = requests.get(url, headers=headers, data=data)
    data = r.json()
    for i in range(len(data)):
        if(data[i]['name'] == module_name):
            return str(data[i]['id'])
        else:
            return 'No Module Found'


#Create a new page within a Canvas course module
def createPageInModule(course_id, headers, page_name, module_name):
    module_id = getModuleId(course_id, headers, module_name)
    url = url_base + course_id + '/modules/' + module_id + '/items'
    page_url = page_name.lower()
    page_url = page_url.replace(' ', '-')
    data = [('module_item[type]', 'Page'),
            ('module_item[title]', page_name),
            ('module_item[page_url]', page_url)]
    r = requests.post(url, headers=headers, data=data)
    return page_url


#Create a new page in a Canvas Course
def createNewPage(course_id, headers, page_name, html_file):
    url = url_base + course_id + '/pages'
    with open(html_file, 'r') as f:
        body = f.read()
        f.close()
    data = [('wiki_page[title]', page_name), ('wiki_page[body]', body),]
    r = requests.post(url, headers=headers, data=data)


#Gets token from hidden file so it will not show up on Git
def getAccessToken():
    token = auth.token
    return token


#Creates pages in Canvas course modulec and adds html content to each page
def createPagesAndAddContent(course_id, headers, page_titles, html_files, module_name):
    assert(len(page_titles) == len(html_files))
    for i in range(len(page_titles)):
        page_url = createPageInModule(course_id, headers, page_titles[i], module_name)
        updateIndividualPage(course_id, headers, page_url, html_files[i])


#Creates pages in Canvas course and adds html content to each page
def createPagesAndAddContent(course_id, headers, page_titles, html_files):
    assert(len(page_titles) == len(html_files))
    for i in range(len(page_titles)):
        page_url = createPage(course_id, headers, page_titles[i])
        updateIndividualPage(course_id, headers, page_url, html_files[i])


if __name__  == '__main__':
    args = selectAction()
    course_id = args.cid
    access_token = getAccessToken()
    headers = {"Authorization": "Bearer " + access_token}
    # course_id = '122'
    url_base = 'https://bscs.instructure.com/api/v1/courses/'

    # '/Users/cameronyee/Desktop/canvas/courses/mhs/courses/te'
    if args.command == 'uc':
        updateCoursePages(args.top_directory)












    # page_url = 'test'
    # html_files = glob('/Users/cameronyee/Desktop/canvas/courses/mhs/courses/te/*.html')
    # page_titles = ['Table of Contents','System Requirements','Using the Course','Lesson 1: Water All Around Us','Lesson 2: Surface Water','Lesson 3: Groundwater','Lesson 4: Watersheds','Lesson 5: Atmosphere','Lesson 6: Oceans','Lesson 7: Human Impacts on Water Resources']
    # module_name = 'Teacher Guide'
    # updateCoursePages(course_id, headers, html_files)
    # storeHtmlData(html_files)
    # module_name = 'Teacher Guide'