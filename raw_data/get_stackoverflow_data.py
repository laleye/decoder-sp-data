import requests, re, sys, json
from datetime import datetime
from bs4 import BeautifulSoup as bs # Scraping webpages
import pandas as pd
from stackapi import StackAPI
from parser_java import normalize_code, parse_annotated_code
from tqdm import tqdm
import argparse


#print(SITE.max_pages, SITE.page_size)
#sys.exit(0)
## Using requests module for downloading webpage content
#response = requests.get('https://stackoverflow.com/tags')

## Parsing html data using BeautifulSoup
#soup = bs(response.content, 'html.parser')

## body 
#body = soup.find('body')

p_href = re.compile('/questions/\d+/')
_answers = list()

def get_code_span(html, match):
    start, end = match.span()
    code = match.group(1)
    start += html[start:end].find(code)
    end = start + len(code)
    return (start, end)


def merge_spans(html, code_spans, sel_spans):
    masks = np.zeros(len(html))
    for start, end in code_spans:
        masks[start:end] += 1.
    for start, end in sel_spans:
        masks[start:end] += 1.
    masks = masks == 2
    for i in range(1, len(html)):
        if html[i].isspace() and masks[i - 1]:
            masks[i] = True
    for i in reversed(range(len(html) - 2)):
        if html[i].isspace() and masks[i + 1]:
            masks[i] = True
    for start, end in code_spans:
        code = [c for c, m in zip(html[start:end], masks[start:end]) if m]
        if len(code) > 0:
            yield ''.join(code)
            
#parse selection ranges to (html_text, start_offset, end_offset)
def parse_range(post_id, selected_range, is_code):
    source, source_id = selected_range['source'].split('-')
    source_id = int(source_id)
    if source == 'title':
        text = titles[source_id]
    else:
        text = posts[source_id]
    start, end = selected_range['start'], selected_range['end']
    return text, start, end

def parse_selection(post_id, selection, is_code):
    ref_text = selection['html']
    sel_spans = []
    source_text = None
    for selected_range in selection['pos']:
        text, start, end = parse_range(post_id, selected_range, is_code)
        if source_text is None:
            source_text = text
        else:
            assert source_text == text
        sel_spans.append((start, end))
    sel_text = '\n'.join(merge_spans(source_text, get_code_spans(source_text, is_code), sel_spans))
    return source_text, sel_text, re.sub('<[^<]+?>', '', ref_text.strip())



def get_code_spans(html, is_code):
    if not is_code:
        return [(0, len(html))]
    matches = re.finditer(r"<pre[^>]*>[^<]*<code[^>]*>((?:\s|[^<]|<span[^>]*>[^<]+</span>)*)</code></pre>", html)
    return [get_code_span(html, m) for m in matches]



def parse_title(title):
    if title.lower().startswith('how ') or title.lower().startswith('what '):
        return title
    if title.strip().endswith('?'):
        return title
    return None
    

def get_body(question_id, answer_id):
    try:
        top_answer = SITE.fetch('questions/' + str(question_id) + '/answers', min=10, sort='votes', filter='withbody')
        for item in top_answer['items']:
            if item['answer_id'] == answer_id and 'body' in item:
                return item['body']
        return None
    except:
        return None
    
def get_all_answers(filename):
    with open('scrap0/stackoverflow_answers_dump_{}.json'.format(filename)) as f:
        answers = json.load(f)
    #answers = list(answers[0])
        
    #print(type(answers))
    #sys.exit(0)
    lst_answers = dict()
    for answer in answers:
        for item in answer['items']:
            lst_answers[item['answer_id']] = item['body'] 
        
    #print(lst_answers)
    return lst_answers
    

def get_code_from_answer(question_id, answer_id, answers):

    if answer_id in answers:
        body = answers[answer_id]
    else:
        body = None
        
    if body is None:
        return []
    

    codes = get_code_spans(body, is_code=True)
    
    if len(codes) == 0:
        return []
    index_lines = codes[0] # to get the first code lines in the answer
        
    return [body[index_lines[0]:index_lines[1]]]
    
    
    
def annotation(qid, question, code):
    return {
        'question_id': qid,
        'intent': question.strip(),
        'snippet': code,
    }
    
def extractQuestions_using_api(page):
    questions = SITE.fetch('questions', fromdate=datetime(2010,10,1), todate=datetime(2020,4,29), sort='votes', page=page, tagged='java')
    
    data = questions['items']
    ids = list()
    for item in tqdm(data, desc='Question Ids extraction', file=sys.stdout, total=len(data)):
        ids.append(item['question_id'])
    
    dt = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    
    #dt = str(datetime(2020,5,1)).replace(' ', '_')
    with open('scrap1/stackoverflow_questions_dump_{}.json'.format(dt), 'w', encoding='utf8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)
        
    
    for id in tqdm(ids, desc='Answer extraction', file=sys.stdout, total=len(ids)):
        top_answers = SITE.fetch('questions/{}/answers'.format(id), min=10, sort='votes', filter='withbody')
        _answers.append(top_answers)
    
    with open('scrap1/stackoverflow_answers_dump_{}.json'.format(dt), 'w', encoding='utf8') as f:
        json.dump(_answers, f, ensure_ascii=False, indent=4)
        
    return questions['page']
    
    
def processed_data(files):
    
    examples = list()
    is_question = 0
    code_in_answer = 0
    is_java_code = 0
    tag_java_with_answer = 0
    all_data = 0
    #for filename in tqdm(files, desc='Process raw data', file=sys.stdout, total=len(files)):
    for filename in files:
        print('Processing of scrap0/stackoverflow_questions_dump_{}.json'.format(filename))
        with open('scrap0/stackoverflow_questions_dump_{}.json'.format(filename)) as f:
            questions = json.load(f)
            
        answers = get_all_answers(filename)
        data = questions['items']
        all_data += len(questions['items'])
        #print(len(data))
        #for item in tqdm(data, desc='Post', file=sys.stdout, total=len(data)):
        for item in data:
            question_id = item['question_id']
            if question_id in [6549821]:
                continue
            example = dict()
            val = 0
            title = parse_title(item['title'])
            #print(title)
            if title is None:
                continue
            is_question += 1
            #if item['tags'][0] == 'java': # take into account if java is the first tag
            if 'java' in item['tags']:    # take into account if java is in the tag list
                val += 1
            if item['is_answered']:
                val += 1
            if 'accepted_answer_id' in item and isinstance(item['accepted_answer_id'], int):
                val += 1
                answer_id = item['accepted_answer_id']
                
            if val == 3:
                tag_java_with_answer += 1
                code = get_code_from_answer(question_id, answer_id, answers)

                if len(title) > 0 and len(code) > 0:
                    code_in_answer += 1
                    code = code[0]
                    code = re.sub('<[^<]+?>', '', code.strip())
                    with open('log_normalization', 'a') as f:
                        code = normalize_code(code, f)
                    #print('code {}'.format(code))
                    if code is not None:
                        is_java_code += 1
                        #if is_java_code == 4:
                            #break
                        examples.append(annotation(question_id, title, code))
    
    print('Number of posts is {}\n'.format(all_data))
    print('Number of questions is {}\n'.format(is_question))
    print('Number of questions which have accepted answer and java as a first tag is {}'.format(tag_java_with_answer))
    print('Number of questions which have code in their accepted answers is {}'.format(code_in_answer))
    print('Number of questions whose the code is a java code is {}\n'.format(is_java_code))
    print('Number of annotated examples is {}'.format(len(examples)))
    
    with open('stackoverflow-java_scrap0_java_in_tags.json', 'w', encoding='utf8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=4)
            
            
            
            
            
def get_answer(url):
    # Using requests module for downloading webpage content
    response = requests.get(url)

    # Parsing html data using BeautifulSoup
    soup = bs(response.content, 'html.parser')
    body= soup.find('body')
    
    print(body)
    

    # Extracting Top Questions
    question_links = body.select("h3 a.question-hyperlink")
    #question_ids = get_questions_id(question_links)
    #error_checking(question_links, question_count)                     # Error Checking
    questions = [i.text for i in question_links]
    print(questions)

def getTags():
    lang_tags = body.find_all('a', class_='post-tag')
    languages = [i.text for i in lang_tags]
    return  languages

def error_checking(list_name, length):
    if (len(list_name) != length):
        print("Error in {} parsing, length not equal to {}!!!".format(list_name, length))
        return -1
    else:
        pass

def get_questions_id(questions):
    qids = dict()
    for i, q in enumerate(questions):
        q = str(q)
        r = re.findall(r'/questions/\d+/', q)
        qid = re.findall(r'\d+', str(r))
        qids[i] = qid[0]
    return qids

def get_top_questions(url, question_count):
    # WARNING: Only enter one of these 3 values [15, 30, 50].
    # Since, stackoverflow, doesn't display any other size questions list
    #url = url + "?sort=votes&pagesize={}".format(question_count)
    url = "https://api.stackexchange.com/docs/questions#fromdate=2020-04-02&todate=2020-05-01&order=desc&sort=activity&filter=default&site=stackoverflow"
    
    # Using requests module for downloading webpage content
    response = requests.get(url)

    # Parsing html data using BeautifulSoup
    soup = bs(response.content, 'html.parser')
    body1 = soup.find('body')
    

    # Extracting Top Questions
    question_links = body1.select("h3 a.question-hyperlink")
    question_ids = get_questions_id(question_links)
    #print(question_links[0])
    error_checking(question_links, question_count)                     # Error Checking
    questions = [i.text for i in question_links]                       # questions list
    
    # Extracting Summary
    summary_divs = body1.select("div.excerpt")
    error_checking(summary_divs, question_count)                       # Error Checking
    summaries = [i.text.strip() for i in summary_divs]                 # summaries list
    
    # Extracting Tags
    tags_divs = body1.select("div.summary > div:nth-of-type(2)")
    
    error_checking(tags_divs, question_count)                          # Error Checking
    a_tags_list = [i.select('a') for i in tags_divs]                   # tag links
    
    tags = []

    for a_group in a_tags_list:
        tags.append([a.text for a in a_group])                         # tags list
    
    # Extracting Number of votes
    vote_spans = body1.select("span.vote-count-post strong")
    error_checking(vote_spans, question_count)                         # Error Checking
    no_of_votes = [int(i.text) for i in vote_spans]                    # votes list
    
    # Extracting Number of answers
    answer_divs = body1.select("div.status strong")
    #print(answer_divs)
    error_checking(answer_divs, question_count)                        # Error Checking
    no_of_answers = [int(i.text) for i in answer_divs]                 # answers list
    
    # Extracting Number of views
    div_views = body1.select("div.supernova")
    
    error_checking(div_views, question_count)                          # Error Checking
    no_of_views = [i['title'] for i in div_views]
    no_of_views = [i[:-6].replace(',', '') for i in no_of_views]
    no_of_views = [int(i) for i in no_of_views]                        # views list
    #print(body1)
    
    # Putting all of them together
    df = pd.DataFrame({'question': questions, 
                       'summary': summaries, 
                       'tags': tags,
                       'no_of_votes': no_of_votes,
                       'no_of_answers': no_of_answers,
                       'no_of_views': no_of_views})

    return df

def post_extraction():
    
    ## question extraction
    page = 51
    while True:
        try:
            page = extractQuestions_using_api(page)
            page = page + 1
        except Exception as e:
            print('Last page: {}'.format(page))
            print(e)
            with open('scrap1/stackoverflow_answers_dump_tmp.json', 'w', encoding='utf8') as f:
                json.dump(_answers, f, ensure_ascii=False, indent=4)
            break
    

def process_data():
    ## processed data
    lst_files0 = ['01_05_2020_02_13_11', '01_05_2020_02_41_19', '01_05_2020_03_32_53', '01_05_2020_03_44_52', '01_05_2020_03_57_02', '01_05_2020_04_08_09', '02_05_2020_17_23_18', '03_05_2020_01_57_49', '03_05_2020_01_58_24']
    processed_data(lst_files0)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--online', action='store_true', help='extract post from stack overflow')
    parser.add_argument('--offline', action='store_true', help='extract title and snippet from dumped data')

    args = parser.parse_args()
    
    if args.online:
        stack_key = "z*Iyq7es6KYXld3DtM3qSw(("
        stack_access_token = "3rI*g4ZjjUUtyZIdMCJzrQ(("

        SITE = StackAPI('stackoverflow', key=stack_key, client_secret=stack_access_token)
        SITE.max_pages = 100
        post_extraction()
    elif args.offline:
        process_data()
    else:
        print('unknow arguments')
        
