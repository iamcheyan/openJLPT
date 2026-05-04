import json

file_path = '/home/tetsuya/Development/openjlpt/data/n2/vocab_reading.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for q in data['questions']:
    # identify English explanation
    if '意味：' in q.get('explanation', '') and count < 5:
        if count == 0:
            q['explanation'] = "1. 正确项分析：句意为“孩子们把新笔记本在桌子上整齐地摆放好”。「揃える」的读音为「そろえる」，意为“使整齐、备齐、使一致”。正确答案为3。\n2. 干扰项分析：选项0「そろえお」、选项1「そろえるい」和选项2「ぞろえる」均为错误拼写，尤其是选项2容易混淆浊音。"
        elif count == 1:
            q['explanation'] = "1. 正确项分析：句意为“关于那一点，我也是那样认为的”。「存じます」的读音为「ぞんじます」，是「思う・知る」的自谦语。正确答案为1。\n2. 干扰项分析：选项0「そんじます」清浊音错误；选项2和3发音错误。"
        elif count == 2:
            q['explanation'] = "1. 正确项分析：句意为“这种布料摸起来非常柔软”。「柔らかい」的读音为「やわらかい」，意为“柔软的”。正确答案为0。\n2. 干扰项分析：选项1、2、3均为拼写干扰项。"
        elif count == 3:
            q['explanation'] = "1. 正确项分析：句意为“他为了实现梦想而拼命努力”。「懸命」的读音为「けんめい」，通常与「一生（いっしょう）」连用，意为“拼命、努力”。正确答案为2。\n2. 干扰项分析：选项0、1、3为发音错误项。"
        elif count == 4:
            q['explanation'] = "1. 正确项分析：句意为“会议的资料已经全部分发完毕”。「配布」的读音为「はいふ」，意为“分发、散发”。正确答案为0。\n2. 干扰项分析：选项1、2、3为汉字读音的常见错误干扰。"
        
        count += 1

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Modified {count} items.")
