"""Generate three original explanatory diagrams (illustrative examples, not measurements).

Run with Python 3. SVG generation uses the standard library. Optional PNG rendering
requires PyMuPDF. SVGs prefer Microsoft YaHei; the renderer uses its available
font fallback. No external image or font is embedded.
"""
from pathlib import Path
from html import escape
import argparse
import math

OUT = Path(__file__).resolve().parent
INK = '#172b4d'
MUTED = '#50647a'
LINE = '#d9e2ec'
BLUE = '#2463b4'
TEAL = '#117c75'
ORANGE = '#b56815'
RED = '#c3393d'
RED_BG = '#fff0f0'
GREEN_BG = '#eaf6f1'
GROUP = {'A': ('#eaf1fc', BLUE), 'B': ('#e9f6f4', TEAL), 'C': ('#fff4e4', ORANGE)}


class SVG:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">'
        ]

    def rect(self, x, y, w, h, fill='white', stroke=LINE, sw=1.5, radius=12, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, text, size=24, fill=INK, weight=400, anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(text)}</text>')

    def line(self, x1, y1, x2, y2, color=LINE, width=2, arrow=False):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')
        if arrow:
            length = math.hypot(x2-x1, y2-y1)
            ux, uy = (x2-x1)/length, (y2-y1)/length
            bx, by = x2 - 10*ux, y2 - 10*uy
            points = f'{x2},{y2} {bx-5*uy},{by+5*ux} {bx+5*uy},{by-5*ux}'
            self.parts.append(f'<polygon points="{points}" fill="{color}"/>')

    def save(self, name):
        p = OUT / f'{name}.svg'
        p.write_text('\n'.join(self.parts + ['</g>', '</svg>']), encoding='utf-8')
        return p


def interleaving():
    s = SVG(1400, 815, '把连续丢包分到不同编码组',
            '同一叶节点的九条数据分为三组，每组三条数据和一条校验。前面连续三个发送位置丢失时，按组发送使A组缺三包；交织发送使每组各缺一包，可分别恢复。')
    s.text(64, 65, '连续漏掉 3 个包，怎样让它们仍可恢复？', 40, weight=700)
    s.text(64, 110, '同一叶节点的 9 条数据分为 A、B、C 三组，每组增加 1 个 XOR 校验包。', 26, MUTED)
    s.text(64, 151, '示意假设：前 3 个发送位置丢包；每组可恢复 1 个已知位置的丢包。', 24, MUTED)
    rows = [
        (188, '按组发：连续丢失集中到 A 组',
         ['A1', 'A2', 'A3', 'AP', 'B1', 'B2', 'B3', 'BP', 'C1', 'C2', 'C3', 'CP'],
         [('A 组缺 3 包：恢复不了', RED), ('B 组完整', TEAL), ('C 组完整', ORANGE)]),
        (444, '交错发：同样的连续丢失分散到三组',
         ['A1', 'B1', 'C1', 'A2', 'B2', 'C2', 'A3', 'B3', 'C3', 'AP', 'BP', 'CP'],
         [('A 组缺 1 包：可恢复', BLUE), ('B 组缺 1 包：可恢复', TEAL), ('C 组缺 1 包：可恢复', ORANGE)])
    ]
    for y, title, packets, summaries in rows:
        s.rect(48, y, 1304, 232)
        s.text(68, y + 42, title, 28, weight=700)
        for i, packet in enumerate(packets):
            x = 68 + 103 * i
            bg, col = GROUP[packet[0]]
            lost = i < 3
            s.text(x + 46, y + 75, str(i + 1), 20, MUTED, anchor='middle')
            s.rect(x, y + 88, 92, 73, RED_BG if lost else bg,
                   RED if lost else col, 2.5 if lost else 1.5, 8,
                   '6 4' if packet.endswith('P') else None)
            s.text(x + 46, y + 119, packet, 25, col, 700, 'middle')
            s.text(x + 46, y + 146, '× 丢失' if lost else ('校验' if packet.endswith('P') else '收到'),
                   19, RED if lost else MUTED, anchor='middle')
        for x, (text, color) in zip([74, 513, 947], summaries):
            s.text(x, y + 206, text, 24, color, 600)
    s.text(64, 721, '改变的是发送次序；两种次序都发 9 个数据包 + 3 个校验包。', 25, INK, 600)
    s.text(64, 764, 'A / B / C 是同一叶节点的编码组。示意例子，非实测结果；XOR 用来说明原理。', 23, MUTED)
    return s.save('01-interleaving'), s.width, s.height


def complementary():
    s = SVG(1400, 805, '辅助接收点是否收到了中心漏掉的包',
            '两个接收点均收到十包中的九包。当它们均漏第四包时，联合仍只得到九包；中心漏第四包而辅助漏第七包时，联合可得到全部十包，随后还需转发第四包给中心。')
    s.text(64, 65, '两个接收点都收到 90%，帮助可能完全不同', 40, weight=700)
    s.text(64, 111, '看逐包记录：辅助接收点收到的，恰好是不是中心漏掉的？', 27, MUTED)
    s.rect(64, 140, 1272, 53, '#f6f8fb', '#f6f8fb')
    s.text(86, 175, '✓ 收到或可从两处取得        × 丢失        本图用 10 个包做示例，非实测。', 24, MUTED)
    for x, helper_missing, title in [(64, 4, '漏的是同一包'), (716, 7, '漏的是不同包')]:
        s.rect(x, 218, 620, 380)
        s.text(x + 24, 263, title, 30, weight=700)
        s.text(x + 24, 302, '包编号', 21, MUTED)
        start = x + 132
        for i in range(1, 11):
            s.text(start + (i-1) * 45 + 19, 302, str(i), 21, MUTED, anchor='middle')
        masks = [({4}, '中心'), ({helper_missing}, '辅助'), ({4} & {helper_missing}, '两处合并')]
        for row, (missing, label) in enumerate(masks):
            y = 324 + row * 72
            s.text(x + 22, y + 31, label, 23, weight=600)
            for i in range(1, 11):
                lost = i in missing
                px = start + (i-1) * 45
                s.rect(px, y, 38, 46, RED_BG if lost else GREEN_BG, RED if lost else '#b4d5c9', 1.5, 6)
                s.text(px + 19, y + 32, '×' if lost else '✓', 29, RED if lost else TEAL, 600, 'middle')
        if helper_missing == 4:
            s.text(x + 24, 565, '合并后仍缺第 4 包：9 / 10', 27, RED, 600)
        else:
            s.text(x + 24, 565, '两处共同拥有全部包：10 / 10', 27, TEAL, 600)
    s.rect(64, 628, 1272, 107, '#f6f8fb', '#f6f8fb')
    s.text(86, 668, '右图的下一步：辅助把第 4 包转发给中心。', 28, BLUE, 600)
    s.text(86, 709, '“两处共同拥有”还需要传输才能变成“中心收到”；反馈和转发都占用时间。', 24, MUTED)
    s.text(64, 776, '接收率相同，互补程度不同。先配对同一批包的收包记录，再评估增加辅助点的收益。', 24, INK)
    return s.save('02-receiver-complementarity'), s.width, s.height


def adaptive_testing():
    s = SVG(1400, 990, '下一轮测试哪一组参数',
            'PS-BAX思路的示意：根据历史测试对未知表现做一次模型抽样，预测A C D合格；从候选中选未知程度最高的D做真实测试，再把结果加入历史。E虽然未知程度很高，本轮抽样预测不合格；下轮重新抽样。')
    s.text(64, 64, '下一次测哪组参数？先选有希望又没测清的组合', 37, weight=700)
    s.text(64, 110, 'PS-BAX 选择思路的组网示意：模型每轮给出一种可能情况，真实测试负责验证。', 25, MUTED)
    s.rect(64, 140, 1272, 70, '#f6f8fb', '#f6f8fb')
    s.text(88, 183, '输入：已测参数 + 整轮用时 + 完整收齐比例；预先设定合格要求。', 26, INK)
    items = [
        ('A', True, '低', '已有较充分数据'),
        ('B', False, '低', '已有较充分数据'),
        ('C', True, '中', '数据较少'),
        ('D', True, '高', '数据较少'),
        ('E', False, '很高', '数据很少'),
    ]
    for i, (name, passes, uncertainty, history) in enumerate(items):
        x = 64 + i * 258
        selected = name == 'D'
        s.rect(x, 245, 240, 310, '#fff6e9' if selected else 'white', ORANGE if selected else LINE,
               3 if selected else 1.5)
        s.text(x + 22, 288, '组合 ' + name, 29, weight=700)
        s.text(x + 22, 329, history, 23, MUTED)
        s.line(x + 20, 348, x + 220, 348)
        s.text(x + 22, 386, '本轮抽样预测', 23, MUTED)
        s.text(x + 22, 429, '合格' if passes else '不合格', 29, TEAL if passes else MUTED, 700)
        s.text(x + 22, 476, '未知程度：' + uncertainty, 23, INK)
        if selected:
            s.rect(x + 16, 497, 208, 40, ORANGE, ORANGE, radius=7)
            s.text(x + 120, 525, '本轮测试 D', 23, 'white', 600, 'middle')
        elif passes:
            s.text(x + 22, 525, '进入本轮候选', 22, TEAL)
        else:
            s.text(x + 22, 525, '本轮未入候选', 22, MUTED)
    s.text(64, 600, '本轮候选是 A、C、D；D 的未知程度最高，所以先测 D。', 28, BLUE, 600)
    boxes = [
        (64, '历史测试记录', '告诉模型已知结果'),
        (392, '抽样并选候选', '本轮选中 D'),
        (720, '做真实组网测试', '测用时和完整收齐比例'),
        (1048, '加入新结果', '下一轮重新选择'),
    ]
    for x, title, detail in boxes:
        s.rect(x, 642, 288, 112, '#f6f8fb', LINE)
        s.text(x + 144, 684, title, 25, INK, 600, 'middle')
        s.text(x + 144, 725, detail, 21, MUTED, anchor='middle')
        if x < 1048:
            s.line(x + 293, 698, x + 319, 698, MUTED, 2, True)
    s.line(1192, 765, 1192, 797, MUTED)
    s.line(1192, 797, 208, 797, MUTED)
    s.line(208, 797, 208, 765, MUTED, arrow=True)
    s.text(64, 852, 'E 这次未入选，下一轮仍会重新抽样。图中的预测与未知程度均为示意。', 24, MUTED)
    s.text(64, 898, '组合指前导码、帧间隔、功率等参数的一个搭配；模型放在电脑上选择下一次测试。', 24, INK)
    s.text(64, 944, '论文用于黑箱算法任务；在组网中使用时，还需定义多项要求和重复测试方式。', 23, MUTED)
    return s.save('03-next-experiment'), s.width, s.height


def render(figures):
    import pymupdf
    for path, width, height in figures:
        with pymupdf.open(path) as document:
            document[0].get_pixmap().save(path.with_suffix('.png'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true', help='also render PNGs with PyMuPDF')
    args = parser.parse_args()
    figures = [interleaving(), complementary(), adaptive_testing()]
    if args.render:
        render(figures)
    for path, width, height in figures:
        print(f'{path.name}: {width} x {height}')
