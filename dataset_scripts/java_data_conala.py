import json 


filename = 'data/java/conala-java.json'
output_anno = 'data/java/conala-java.anno'
output_code = 'data/java/conala-java.code'

def get_annotations(elt):
    if 'title' in elt and elt['title'] is not None:
        return elt['annotations']
    return None
            

def load_conala_data(jsonfile):
    with open(jsonfile) as f:
        data = json.load(f)
    queries = list()
    codes = list()
    #print(data)
    print('len of data in {} is {}'.format(jsonfile, len(data)))
    if len(data) > 0:
        examples = list()
        for elt in data:
            if isinstance(elt, dict):
                annotations = get_annotations(elt)
                title = elt['title']
                if annotations is not None:
                    example = dict()
                    for i, annotation in enumerate(annotations):
                        intent = annotation['intent']
                        if len(intent.strip()) > 0:
                            queries.append(intent)
                            example['intent'] = intent
                        else:
                            queries.append(title)
                            example['intent'] = title
                        code = annotation['normalized_code_snippet']
                        codes.append(code)
                        example['snippet'] = code
                        examples.append(example)
                        
                        #if annotation['normalized_code_snippet'].strip() != annotation['code_snippet'].strip():
                            #print('normalization code problem at {} title: {}'.format(i, title))

    print('Number of examples: {}'.format(len(examples)))
    with open('data/conala-java-processed.json', 'w', encoding='utf8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=4)
    #print(queries)
    #with open(output_anno, 'w') as f:
        #for nl in queries:
            #f.write(nl+'\n')
    
    #with open(output_code, 'w') as f:
        #for cd in codes:
            #f.write(cd+'\n')
            
load_conala_data(filename)

