# -*- coding: utf-8 -*-
import csv
import configparser
import os.path
from collections import Counter

utau = configparser.RawConfigParser(comment_prefixes=("UST", "#", ";"))
utau.optionxform = str
utau.read("project.ust")

# 駅名,読み,県,会社+路線,地図
with open("table.csv", newline="") as file:
    temp = list(csv.reader(file))

data = []
kansou = []
for item in temp:
    if not item or not len(item) or not item[0]:
        kansou += [len(data)]
        continue
    if item[0][-1] == ")":
        item[0] = item[0].replace("(", "<s80> (")
    elif item[0][-1] == "]":
        item[0] = item[0][:item[0].index("[")]
    data += [item]

fps = 60
template = """%s
<p+0,200><#ffff00><s80,ヒラギノ角ゴ ProN W3>%s
<p+0,+10><#80ffc0><s64,ヒラギノ丸ゴ ProN W4>%s
<p+0,+5><#ff80ff><s64,ヒラギノ丸ゴ ProN W4>%s"""

output = configparser.RawConfigParser()
output.optionxform = str
output.add_section("exedit")
output["exedit"] = {
    "width": 1920,
    "height": 1080,
    "rate": fps,
    "scale": 1,
    "audio_rate": 44100,
    "audio_ch": 2,
}

multipler = fps / utau.getfloat("#SETTING", "Tempo") / 8

colors = ["ffffff", "ff0000", "00ff00", "0000ff", "ffc000", "0080ff", "ff0080", "c000ff",
          "804000", "200080", "8080ff", "ff8080", "80ff80", "e080ff", "ffe080", "80e0ff"]
prefs = ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県",
         "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県",
         "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
         "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]
counter = Counter({pref: 0 for pref in prefs})

j = 0
last = 0
map_start = 0
alt = False
map_alt = False
lowest = 0
prev_yokoku = {}
prev_map = None


def pref_abbr(pref):
    return pref[:-1] if pref[-1] in "都府県" else pref


def tohex(text):
    return text.ljust(1024, "\0").encode("utf-16le").hex()


def map_num(index):
    if not index:
        return "000"
    try:
        return "%03d" % int(data[index - 1][-1])
    except ValueError:
        return data[index - 1][-1]


def write_text(index, start, end):
    global j, last, map_start, alt, map_alt, prev_map, lowest, prev_yokoku

    this = round(start * multipler)

    if index in kansou and this - last >= fps * 3:
        write_kansou(last, this)

    # 前の地図画像
    curr_map = map_num(index)
    if curr_map and prev_map != curr_map:
        prev_map = curr_map
        output.add_section(str(j))
        output[str(j)] = {
            "start": map_start + 1,
            "end": this,
            "layer": 8 if map_alt else 7,
            "overlay": 1,
            "camera": 0,
        }
        output.add_section("%d.0" % j)
        output["%d.0" % j] = {
            "_name": "画像ファイル",
            "file": os.path.abspath(f"地図/{curr_map}.png"),
        }
        output.add_section("%d.1" % j)
        output["%d.1" % j] = {
            "_name": "マスク",
            "元のサイズに合わせる": 1,
            "type": 0,
            "name": "*" + os.path.abspath("../垰瀬内新雛形地図マスク4.png"),
            "mode": 0,
        }
        output.add_section("%d.2" % j)
        output["%d.2" % j] = {
            "_name": "標準描画",
            "X": 427.0,
            "Y": -148.0,
            "Z": 0.0,
            "拡大率": 64.0,
        }
        j += 1
        map_start = this
        map_alt = not map_alt
    last = round(end * multipler)
    counter[data[index][2]] += 1

    # 駅名
    alt = not alt
    output.add_section(str(j))
    output[str(j)] = {
        "start": this + 1,
        "end": last,
        "layer": 6 if alt else 5,
        "overlay": 1,
        "camera": 0,
    }
    output.add_section("%d.0" % j)
    output["%d.0" % j] = {
        "_name": "テキスト",
        "サイズ": 160,
        "type": 4,  # 縁取り文字(細)
        "color": "00ff00",
        "color2": "000000",
        "align": 1,  # 中央揃え[中]
        "font": "ヒラギノ角ゴ ProN W3",
        "text": tohex(template % tuple(data[index][:-1])),
    }
    output.add_section("%d.1" % j)
    output["%d.1" % j] = {
        "_name": "標準描画",
        "X": 0.0,
        "Y": -320.0,
        "Z": 0.0,
    }
    j += 1

    # 全県制覇
    count = counter.most_common()
    highest = count[0][1]
    if lowest != count[-1][1]:
        lowest += 1
        output.add_section(str(j))
        output[str(j)] = {
            "start": this + 1,
            "end": this + fps * 3,  # 3秒
            "layer": 3,
            "overlay": 1,
            "camera": 0,
        }
        output.add_section("%d.0" % j)
        output["%d.0" % j] = {
            "_name": "テキスト",
            "サイズ": 60,
            "type": 4,  # 縁取り文字(細)
            "color": colors[lowest],
            "color2": "000000",
            "align": 7,  # 中央揃え[下]
            "font": "ヒラギノ角ゴ ProN W3",
            "text": tohex(f"※全県{lowest}周制覇"),
        }
        output.add_section("%d.1" % j)
        output["%d.1" % j] = {
            "_name": "アニメーション効果",
            "track0": 1.0,
            "track1": 50.0,
            "track2": 100.0,
            "track3": 100.0,
            "check0": 0,
            "type": 17,  # 点滅
            "filter": 0,
            "name": "",
            "param": "",
        }
        output.add_section("%d.2" % j)
        output["%d.2" % j] = {
            "_name": "標準描画",
            "X": 480.0,
            "Y": -70.0,
            "Z": 0.0,
        }
        j += 1

    # 予告
    yokoku = ""
    if count[0][0] == data[index][2] and highest != count[1][1] and highest > 1:
        # 1番乗り
        yokoku += f"<#{colors[highest]}>{highest}駅登場1番乗り:{pref_abbr(count[0][0])}\r\n"

    nokori = 0
    while highest > lowest:
        # 制覇まで残り数回
        while count[nokori][1] == highest:
            nokori += 1
        if nokori >= 37 and (highest not in prev_yokoku or prev_yokoku[highest] != nokori):
            append = ""
            if nokori >= 43:
                append = "(" + "･".join(
                    map(pref_abbr, next(zip(*count[nokori:])))) + ")"
                if nokori == 43:
                    append = "<s40>" + append + "<s>"
            yokoku += f"<#{colors[highest]}>{highest}周制覇まで残り{47 - nokori}県{append}\r\n"
            prev_yokoku[highest] = nokori
        highest -= 1

    if yokoku:
        output.add_section(str(j))
        output[str(j)] = {
            "start": this + 1,
            "end": last,
            "layer": 4,
            "overlay": 1,
            "camera": 0,
        }
        output.add_section("%d.0" % j)
        output["%d.0" % j] = {
            "_name": "テキスト",
            "サイズ": 48,
            "type": 4,  # 縁取り文字(細)
            "align": 6,  # 左寄せ[下]
            "font": "ヒラギノ角ゴ ProN W3",
            "text": tohex(yokoku),
        }
        output.add_section("%d.1" % j)
        output["%d.1" % j] = {
            "_name": "標準描画",
            "X": -600.0,
            "Y": 360.0,
            "Z": 0.0,
        }
        j += 1


def write_kansou(start, end):
    global j, lowest

    count = counter.most_common()
    highest = count[0][1]

    # 予告
    yokoku = ""
    nokori = 0
    while highest > lowest:
        while count[nokori][1] == highest:
            nokori += 1
        append = ""
        if nokori >= 43:
            append = "\r\n  (" + "･".join(
                map(pref_abbr, next(zip(*count[nokori:])))) + ")"
        yokoku += f"<#{colors[highest]}>■全県{highest}周制覇まで残り{47 - nokori}県{append}\r\n"
        highest -= 1
    while highest:
        yokoku += f"<#{colors[highest]}>■全県{highest}周制覇完了\r\n"
        highest -= 1

    output.add_section(str(j))
    output[str(j)] = {
        "start": start + 1,
        "end": end,
        "layer": 4,
        "overlay": 1,
        "camera": 0,
    }
    output.add_section("%d.0" % j)
    output["%d.0" % j] = {
        "_name": "テキスト",
        "サイズ": 48,
        "type": 4,  # 縁取り文字(細)
        "align": 6,  # 左寄せ[下]
        "font": "ヒラギノ角ゴ ProN W3",
        "text": tohex(yokoku),
    }
    output.add_section("%d.1" % j)
    output["%d.1" % j] = {
        "_name": "標準描画",
        "X": -600.0,
        "Y": 360.0,
        "Z": 0.0,
    }
    j += 1


kanas = "あいうえおかきくけこがぎぐげごさしすせそざじずぜぞたちつてとだぢづでどなにぬねのはひふへほばびぶべぼぱぴぷぺぽまみむめもや𛀆ゆ𛀁よらりるれろわゐ𛄟ゑを"
sutegana = "ぁぃぅぇぉゃ ゅ ょ𛅐𛅐 𛅑𛅒"
youon = "ぁぃぅぇぉ"
kaiyouon = "ゃ ゅ ょ"
gouyouon = "𛅐𛅐 𛅑𛅒"
replacement = [("ぢ", "じ"), ("づ", "ず"), ("いぁ", "や"), ("いぃ", "𛀆"), ("いぅ", "ゆ"), ("いぇ", "𛀁"),
               ("いぉ", "よ"), ("うぁ", "わ"), ("うぃ", "ゐ"), ("うぅ", "𛄟"), ("うぇ", "ゑ"), ("うぉ", "を")]

stations = []

for index, item in enumerate(data):
    reading = item[1]
    c = 0
    while c < len(reading):
        start = c
        norm = reading[c]
        if reading[c] in "ーっん":
            vowel = -1
            c += 1
        else:
            try:
                vowel = kanas.index(reading[c]) % 5
                c += 1
            except Exception:
                raise ValueError(
                    f"#{index} {item[0]}（{reading}）：該当しない文字を検出しました：{reading[c]}")
            else:
                while True:
                    try:
                        assert reading[c] != " "
                        normalize = (vowel == 1 and reading[c] in kaiyouon) or (
                            vowel == 2 and reading[c] in gouyouon)
                        vowel = sutegana.index(reading[c]) % 5
                        norm += youon[vowel] if normalize else reading[c]
                        c += 1
                    except Exception:
                        break
                for left, right in replacement:
                    if norm.startswith(left):
                        norm = right + norm[len(left):]
                        break
        stations += [{
            "index": index,
            "mora": reading[start:c],
            "norm": norm,
            "vowel": vowel,
            "start": start,
            "end": c
        }]

lyrics = []

i = 0
time = 0
section = "#%04d" % i
while utau.has_section(section):
    lyric = utau.get(section, "Lyric")
    c = 0
    norm = lyric[c]
    if lyric[c] in "ーっん":
        vowel = -1
        c += 1
    else:
        try:
            vowel = kanas.index(lyric[c]) % 5
            c += 1
        except Exception:
            pass
        else:
            while True:
                try:
                    assert lyric[c] != " "
                    normalize = (vowel == 1 and lyric[c] in kaiyouon) or (
                        vowel == 2 and lyric[c] in gouyouon)
                    vowel = sutegana.index(lyric[c]) % 5
                    norm += youon[vowel] if normalize else lyric[c]
                    c += 1
                except Exception:
                    break
            for left, right in replacement:
                if norm.startswith(left):
                    norm = right + norm[len(left):]
                    break
    end = time + utau.getint(section, "Length")
    if c > 0:
        lyrics += [{
            "index": i,
            "mora": lyric[:c],
            "norm": norm,
            "vowel": vowel,
            "start": time,
            "end": end
        }]
    time = end
    i += 1
    section = "#%04d" % i


def skippable(a, b):
    if b["vowel"] == -1:
        return True
    if b["norm"] not in "あいうえお":
        return False
    a = a["vowel"]
    b = b["vowel"]
    return a == b or a == 3 and b == 1 or a == 4 and b == 2


li = 0
si = 0
start = lyrics[0]["start"]
index = 0
while li < len(lyrics) and si < len(stations):
    while li < len(lyrics) and si < len(stations):
        mora = lyrics[li]["norm"]
        if mora == stations[si]["norm"]:
            if mora in "あいうえお":
                lj = 1
                while li + lj < len(lyrics) and lyrics[li + lj]["norm"] == mora:
                    lj += 1
                sj = 1
                while si + sj < len(stations) and stations[si + sj]["norm"] == mora:
                    sj += 1
                if si + sj >= len(stations) or stations[si + sj]["index"] <= stations[si]["index"] + 1:
                    si += max(0, sj - lj)
                    li += max(0, lj - sj)
            break
        if si:
            if skippable(stations[si - 1], lyrics[li]):
                if skippable(stations[si - 1], stations[si]):
                    sk = si + 1
                    while sk < len(stations) and stations[sk]["norm"] == stations[si]["norm"]:
                        sk += 1
                    if sk < len(stations) and stations[sk]["norm"] == lyrics[li]["norm"] and stations[sk]["index"] <= stations[si]["index"] + 1:
                        si = sk
                        continue
                li += 1
                continue
            if skippable(stations[si - 1], stations[si]):
                si += 1
                continue
        raise ValueError(
            f"{data[index][0]}（{data[index][1]}）：歌詞と駅名が一致しません：#{lyrics[li]['index']:04d} {lyrics[li]['mora']} vs {stations[si]['mora']}")
    if si and index != stations[si]["index"]:
        write_text(index, start, lyrics[li - 1]["end"])
        start = lyrics[li]["start"]
        index += 1
        assert index == stations[si]["index"], f"{data[index][0]}（{data[index][1]}）：駅が飛ばされました"
    li += 1
    si += 1
write_text(index, start, lyrics[li - 1]["end"])

# 最後の地図画像
curr_map = map_num(index + 1)
if curr_map and prev_map != curr_map:
    output.add_section(str(j))
    output[str(j)] = {
        "start": map_start + 1,
        "end": last,
        "layer": 8 if map_alt else 7,
        "overlay": 1,
        "camera": 0,
    }
    output.add_section("%d.0" % j)
    output["%d.0" % j] = {
        "_name": "画像ファイル",
        "file": os.path.abspath(f"地図/{curr_map}.png"),
    }
    output.add_section("%d.1" % j)
    output["%d.1" % j] = {
        "_name": "マスク",
        "元のサイズに合わせる": 1,
        "type": 0,
        "name": "*" + os.path.abspath("../垰瀬内新雛形地図マスク4.png"),
        "mode": 0,
    }
    output.add_section("%d.2" % j)
    output["%d.2" % j] = {
        "_name": "標準描画",
        "X": 427.0,
        "Y": -148.0,
        "Z": 0.0,
        "拡大率": 64.0,
    }

output["exedit"]["length"] = str(last)

with open("object.exo", "w") as file:
    output.write(file, space_around_delimiters=False)

assert li >= len(lyrics), "ファイルは正常に書き出しましたが歌詞が余っています"
assert si >= len(stations), "ファイルは正常に書き出しましたが駅名が余っています"
print("ファイルは正常に書き出しました")
