import os
import fnmatch
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import font
from tkinter import ttk
import threading

try:
    import pyperclip
    pyperclip_available = True
except ImportError:
    pyperclip_available = False

class ReadmeGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("README 생성기")
        master.geometry("1024x720")
        master.resizable(True, True)

        self.folder_path = ""
        self.ignore_patterns = []
        self.ignore_dirs = []

        # Tkinter 기본 폰트 설정
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=16)

        # 메인 프레임 생성
        frame = tk.Frame(master)
        frame.pack(fill=tk.BOTH, expand=True)

        # 버튼 프레임
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        # 버튼 프레임의 열(column) 가중치 설정
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        # 폴더 선택 버튼
        self.select_button = tk.Button(
            button_frame, text="폴더 선택", command=self.select_folder, font=self.default_font
        )
        self.select_button.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 내용 읽어들이기 버튼
        self.generate_button = tk.Button(
            button_frame, text=" 내용 읽어들이기", command=self.generate_readme, font=self.default_font
        )
        self.generate_button.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 결과 복사하기 버튼
        self.copy_button = tk.Button(
            button_frame, text="결과 복사하기", command=self.copy_content, font=self.default_font
        )
        self.copy_button.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        # 진행 바 추가
        self.progress = ttk.Progressbar(frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)

        # 내용 표시 영역
        self.text_area = scrolledtext.ScrolledText(frame, font=self.default_font)
        self.text_area.pack(pady=5, fill=tk.BOTH, expand=True)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            messagebox.showinfo("폴더 선택됨", f"선택한 폴더: {self.folder_path}")
            self.load_ignore_patterns()

    def load_ignore_patterns(self):
        self.ignore_patterns = []
        self.ignore_dirs = []
        gitignore_path = os.path.join(self.folder_path, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    pattern = line.strip()
                    if pattern and not pattern.startswith('#'):
                        if pattern.endswith('/'):
                            # 디렉토리 패턴
                            self.ignore_dirs.append(pattern)
                        else:
                            self.ignore_patterns.append(pattern)
            messagebox.showinfo(
                "무시 패턴 로드됨",
                f"{len(self.ignore_patterns)}개의 파일 패턴과 {len(self.ignore_dirs)}개의 디렉토리 패턴이 무시됩니다."
            )

    def generate_readme(self):
        if not self.folder_path:
            messagebox.showwarning("폴더 선택 필요", "먼저 폴더를 선택하세요.")
            return

        # 진행 바 초기화
        self.progress['value'] = 0
        self.progress['maximum'] = 100  # 최대 값을 100으로 설정

        # 별도의 스레드에서 작업 수행
        threading.Thread(target=self.generate_readme_thread).start()

    def generate_readme_thread(self):
        # 총 파일 수 계산
        total_files = self.count_files(self.folder_path)
        processed_files = 0

        content = ""
        for root, dirs, files in os.walk(self.folder_path, topdown=True):
            # 무시할 디렉토리 처리
            dirs[:] = [
                d for d in dirs
                if not self.is_dir_ignored(os.path.relpath(os.path.join(root, d), self.folder_path))
            ]
            # 무시할 파일 처리
            files = [
                f for f in files
                if not self.is_file_ignored(os.path.relpath(os.path.join(root, f), self.folder_path))
            ]

            # 폴더 구조 생성
            level = os.path.relpath(root, self.folder_path).count(os.sep)
            indent = ' ' * 4 * level
            content += f"{indent}{os.path.basename(root)}/\n"

            for file in files:
                filepath = os.path.join(root, file)
                sub_indent = ' ' * 4 * (level + 1)
                content += f"{sub_indent}{file}\n"

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    # 파일 내용 추가
                    file_lines = file_content.splitlines()
                    for line in file_lines:
                        content += f"{sub_indent}{line}\n"
                except Exception as e:
                    content += f"{sub_indent}파일을 읽을 수 없습니다: {e}\n"

                processed_files += 1
                progress_value = (processed_files / total_files) * 100
                self.update_progress(progress_value)

        # 작업 완료 후 텍스트 영역 업데이트
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.END, content)
        messagebox.showinfo("생성 완료", "README 내용이 생성되었습니다.")
        self.progress['value'] = 0  # 진행 바 초기화

    def count_files(self, folder_path):
        count = 0
        for root, dirs, files in os.walk(folder_path, topdown=True):
            # 무시할 디렉토리 처리
            dirs[:] = [
                d for d in dirs
                if not self.is_dir_ignored(os.path.relpath(os.path.join(root, d), folder_path))
            ]
            # 무시할 파일 처리
            files = [
                f for f in files
                if not self.is_file_ignored(os.path.relpath(os.path.join(root, f), folder_path))
            ]
            count += len(files)
        return count

    def update_progress(self, value):
        # GUI 업데이트는 메인 스레드에서 수행해야 함
        self.progress.after(0, lambda: self.progress.config(value=value))

    def is_file_ignored(self, path):
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def is_dir_ignored(self, path):
        for pattern in self.ignore_dirs:
            # 디렉토리 패턴 매칭
            if path == pattern.rstrip('/'):
                return True
            if path.startswith(pattern):
                return True
        return False

    def copy_content(self):
        content = self.text_area.get('1.0', tk.END)
        if pyperclip_available:
            pyperclip.copy(content)
            messagebox.showinfo("복사 완료", "내용이 클립보드에 복사되었습니다.")
        else:
            self.master.clipboard_clear()
            self.master.clipboard_append(content)
            messagebox.showinfo("복사 완료", "내용이 클립보드에 복사되었습니다.")

    # 창을 화면 중앙에 배치하는 함수 (선택 사항)
    def center_window(self):
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    app = ReadmeGeneratorGUI(root)
    # 창을 화면 중앙에 배치 (선택 사항)
    # app.center_window()
    root.mainloop()
