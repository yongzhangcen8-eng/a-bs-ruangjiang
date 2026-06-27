import flet as ft
import random
import re
import json
import os

class MobileFlashcardApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "高效背单词 (手机版)"
        # 调整为类似手机屏幕的预览比例
        self.page.window_width = 390
        self.page.window_height = 844
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        # 数据存储
        self.word_bank = []
        self.total_words_in_round = 0
        self.wrong_words = set()
        self.current_word = None
        
        # 手机端本地沙盒存储路径
        self.db_file = os.path.join(self.page.client_storage.get("app_dir") or ".", "wrong_words_mobile.json")
        self.load_wrong_words()
        
        # 初始化 UI 组件
        self.build_ui()

    def load_wrong_words(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.wrong_words = set((item[0], item[1]) for item in data)
            except:
                self.wrong_words = set()

    def save_wrong_words(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(list(self.wrong_words), f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存储失败: {e}")

    def count_chinese(self, text):
        return len(re.findall(r'[\u4e00-\u9fa5]', text))

    def build_ui(self):
        # 顶部状态栏
        self.lbl_status = ft.Text(f"历史错词: {len(self.wrong_words)} 个", color=ft.colors.PURPLE, size=14, weight=ft.FontWeight.BOLD)
        
        # 顶部导入抽屉输入框 (代替Word选择弹窗，更适合手机)
        self.txt_import_input = ft.TextField(label="粘贴通过AI处理好的规范单词文本", multiline=True, min_lines=3, max_lines=5, hint_text="例：\n团圆饭: family reunion dinner\n京剧: Peking opera")
        
        # 进度条 (正中间最上方)
        self.lbl_progress = ft.Text("剩余单词: -- / --", size=16, color=ft.colors.GREY_600)
        
        # 单词展示卡片
        self.lbl_question = ft.Text("请点击下方按钮粘贴导入单词", size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        self.lbl_answer = ft.Text("", size=22, color=ft.colors.BLUE, italic=True, text_align=ft.TextAlign.CENTER)
        
        # 按钮容器
        self.btn_container = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        # 常驻功能按钮 (复习错题/重置)
        self.btn_wrong_pool = ft.ElevatedButton("复习错题本", on_click=self.switch_to_wrong_pool, bgcolor=ft.colors.DEEP_ORANGE_50)
        
        # 组装页面
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Row([self.lbl_status, self.btn_wrong_pool], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    self.txt_import_input,
                    ft.ElevatedButton("确认导入单词", on_click=self.import_text_data, bgcolor=ft.colors.GREEN_500, color=ft.colors.WHITE),
                    ft.Divider(),
                    ft.Column([
                        self.lbl_progress,
                        ft.Container(height=30),
                        self.lbl_question,
                        ft.Container(height=20),
                        self.lbl_answer,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                    ft.Container(content=self.btn_container, margin=ft.margin.only(bottom=40))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                padding=20
            )
        )
        self.show_stage0()

    def show_stage0(self):
        self.btn_container.controls = []
        self.page.update()

    def show_stage1(self):
        """显示：认识 / 不认识"""
        self.btn_container.controls = [
            ft.ElevatedButton("认识", on_click=self.click_know, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE, width=120, height=45),
            ft.ElevatedButton("不认识", on_click=self.click_dont_know, bgcolor=ft.colors.PINK, color=ft.colors.WHITE, width=120, height=45)
        ]
        self.page.update()

    def show_stage2(self):
        """显示：下一个 / 需要review"""
        self.btn_container.controls = [
            ft.ElevatedButton("下一个", on_click=self.click_next, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, width=120, height=45),
            ft.ElevatedButton("需要review", on_click=self.click_review, bgcolor=ft.colors.ORANGE, color=ft.colors.WHITE, width=120, height=45)
        ]
        self.page.update()

    def show_dont_know_stage(self):
        """显示不认识：只有“下一个”"""
        self.btn_container.controls = [
            ft.ElevatedButton("下一个", on_click=self.click_next, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, width=200, height=45)
        ]
        self.page.update()

    def import_text_data(self, e):
        raw_text = self.txt_import_input.value.strip()
        if not raw_text:
            return
        
        self.word_bank = []
        lines = raw_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line: continue
            line = re.sub(r"^[\d\.\s、\-①②③④⑤⑥⑦⑧⑨⑩]+", "", line).strip()
            line = line.replace("：", ":")
            if ":" not in line: continue
            
            parts = line.split(":", 1)
            part_a = parts[0].strip()
            part_b = parts[1].strip()
            
            if self.count_chinese(part_a) > self.count_chinese(part_b):
                chn, eng = part_a, part_b
            else:
                chn, eng = part_b, part_a
                
            eng = "".join(re.findall(r"[a-zA-Z\s\-\(\);,']+", eng)).strip()
            chn = chn.strip()
            if eng and chn:
                self.word_bank.append((eng, chn))
                
        if self.word_bank:
            self.total_words_in_round = len(self.word_bank)
            self.txt_import_input.visible = False # 导入成功后隐藏输入框释放手机空间
            self.next_word()
        else:
            self.lbl_question.value = "导入失败，请检查格式"
            self.page.update()

    def update_progress_label(self):
        if self.current_word is None and len(self.word_bank) == 0:
            self.lbl_progress.value = "剩余单词: 0 / 0"
            self.lbl_progress.color = ft.colors.GREY_600
        else:
            remaining = len(self.word_bank) + (1 if self.current_word else 0)
            self.lbl_progress.value = f"剩余单词: {remaining} / {self.total_words_in_round}"
            self.lbl_progress.color = ft.colors.ORANGE_700 if remaining <= 5 else ft.colors.GREEN_600
        self.page.update()

    def next_word(self):
        if not self.word_bank:
            self.current_word = None
            self.lbl_question.value = "本轮全部背完啦！🎉"
            self.lbl_answer.value = ""
            self.txt_import_input.visible = True # 结束了重新放出输入框
            self.update_progress_label()
            self.show_stage0()
            return
            
        self.current_word = random.choice(self.word_bank)
        self.lbl_question.value = self.current_word[0] # 显英文
        self.lbl_answer.value = ""
        self.update_progress_label()
        self.show_stage1()

    def click_know(self, e):
        if not self.current_word: return
        self.lbl_answer.value = self.current_word[1]
        self.show_stage2()

    def click_dont_know(self, e):
        if not self.current_word: return
        self.wrong_words.add(self.current_word)
        self.save_wrong_words()
        self.lbl_status.value = f"历史错词: {len(self.wrong_words)} 个"
        self.lbl_answer.value = self.current_word[1]
        self.show_dont_know_stage()

    def click_next(self, e):
        if not self.current_word: return
        if self.current_word in self.word_bank:
            self.word_bank.remove(self.current_word)
        self.next_word()

    def click_review(self, e):
        if not self.current_word: return
        self.wrong_words.add(self.current_word)
        self.save_wrong_words()
        self.lbl_status.value = f"历史错词: {len(self.wrong_words)} 个"
        if self.current_word in self.word_bank:
            self.word_bank.remove(self.current_word)
        self.next_word()

    def switch_to_wrong_pool(self, e):
        self.load_wrong_words()
        if not self.wrong_words:
            self.lbl_question.value = "没有历史错词记录！"
            self.page.update()
            return
        self.word_bank = list(self.wrong_words)
        self.total_words_in_round = len(self.word_bank)
        self.txt_import_input.visible = False
        self.next_word()

def main(page: ft.Page):
    MobileFlashcardApp(page)

if __name__ == "__main__":
    # 可以在电脑上本地像网页一样调试预览
    ft.app(target=main)