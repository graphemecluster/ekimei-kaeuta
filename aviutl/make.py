# -*- coding: utf-8 -*-
import csv
import configparser

utau = configparser.RawConfigParser(comment_prefixes=("UST", "#", ";"))
utau.optionxform = str
utau.read("project.ust")

# 駅名,読み,県,会社+路線
with open("table.csv", newline="") as file:
    data = list(csv.reader(file))

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

j = 0
last = 0


def write_text(text, start, end):
    global j, last
    last = round(end * multipler)
    output.add_section(str(j))
    output[str(j)] = {
        "start": round(start * multipler) + 1,
        "end": last,
        "layer": 1,
        "overlay": 1,
        "camera": 0,
    }
    output.add_section("%d.0" % j)
    output["%d.0" % j] = {
        "_name": "テキスト",
        # "サイズ": 200,
        # "type": 4,  # 縁取り文字（細）
        # "color": "00ff00",
        # "color2": "000000",
        # "align": 4,  # 中央揃え［中］
        # "spacing_x": 0,
        # "spacing_y": 20,
        # "font": "ヒラギノ角ゴ ProN W3",
        "text": text.ljust(1024, "\0").encode("utf-16le").hex(),
    }
    output.add_section("%d.1" % j)
    output["%d.1" % j] = {
        "_name": "標準描画",
        # "拡大率": 120,
        # "X": 0.0,
        # "Y": 0.0,
        # "Z": 0.0,
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
                if stations[si + sj]["index"] <= stations[si]["index"] + 1:
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
        write_text(template % tuple(data[index]), start, lyrics[li - 1]["end"])
        start = lyrics[li]["start"]
        index += 1
        assert index == stations[si]["index"], f"{data[index][0]}（{data[index][1]}）：駅が飛ばされました"
    li += 1
    si += 1
write_text(template % tuple(data[index]), start, lyrics[li - 1]["end"])

output["exedit"]["length"] = str(last)

with open('object.exo', 'w') as file:
    output.write(file, space_around_delimiters=False)

assert li >= len(lyrics), "ファイルは正常に書き出しましたが歌詞が余っています"
assert si >= len(stations), "ファイルは正常に書き出しましたが駅名が余っています"
print("ファイルは正常に書き出しました")
