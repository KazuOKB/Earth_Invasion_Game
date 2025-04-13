import tkinter as tk
from PIL import Image, ImageTk

class TopPanel(tk.Frame):
    def __init__(self, master, controller=None):
        super().__init__(master)
        self.controller = controller
        self.width = 750
        self.height = 500
        
        # Canvas を作成（背景および配置用）
        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.pack(fill="both", expand=True)
        
        # 画像の読み込みと変換
        # ※画像ファイル（haikei.png, earth2.png, ufo004.png）は実行ディレクトリに配置してください
        try:
            self.haikei_img = Image.open("images/haikei.png").resize((self.width, self.height))
            self.haikei_photo = ImageTk.PhotoImage(self.haikei_img)
            
            self.earth_img = Image.open("images/earth2.png")
            self.earth_photo = ImageTk.PhotoImage(self.earth_img)
            
            self.ufo_img = Image.open("images/ufo004.png")
            self.ufo_photo = ImageTk.PhotoImage(self.ufo_img)
        except Exception as e:
            print("画像読み込みエラー:", e)
            exit(1)
        
        # 背景画像をキャンバスに描画（左上に配置）
        self.canvas.create_image(0, 0, image=self.haikei_photo, anchor="nw")
        
        # Java の paintComponent に相当する描画
        # Earth: Java では (d.width - 220, d.height - 180) → (750-220, 500-180) = (530, 320)
        self.canvas.create_image(530, 320, image=self.earth_photo, anchor="nw")
        # UFO: Java では (20,20)
        self.canvas.create_image(20, 20, image=self.ufo_photo, anchor="nw")
        
        # ボタンの作成（Java の btn1: "Gameスタート", btn3: "Gameの説明"）
        # なお、ボタンの枠線は relief="solid" と borderwidth=4 で実現
        self.btn1 = tk.Button(self, text="Gameスタート", command=self.game_start,
                              relief="solid", borderwidth=4)
        self.btn3 = tk.Button(self, text="Gameの説明", command=self.game_explanation,
                              relief="solid", borderwidth=4)
        # Java では btn1 の位置は (100,290,200,40), btn3 は (100,390,200,40)
        self.canvas.create_window(100, 290, anchor="nw", window=self.btn1, width=200, height=40)
        self.canvas.create_window(100, 390, anchor="nw", window=self.btn3, width=200, height=40)
        
        # ラベルの作成（Java では 3 つのラベル "U", "V", "E"）
        # 配置位置は Java と同様に、gametitle1: (395,55,200,200), 
        # gametitle2: (510,55,200,200), gametitle3: (560,55,200,200)
        # 色は RGB(255,60,0) → "#FF3C00"
        label_color = "#FF3C00"
        self.gametitle1 = tk.Label(self, text="U", fg=label_color, bg="white")
        self.gametitle1.config(font=("Serif", 200, "bold"))
        
        self.gametitle2 = tk.Label(self, text="V", fg=label_color, bg="white")
        self.gametitle2.config(font=("Serif", 100, "bold"))
        
        self.gametitle3 = tk.Label(self, text="E", fg=label_color, bg="white")
        self.gametitle3.config(font=("Serif", 200, "bold"))
        
        self.canvas.create_window(395, 55, anchor="nw", window=self.gametitle1, width=200, height=200)
        self.canvas.create_window(510, 55, anchor="nw", window=self.gametitle2, width=200, height=200)
        self.canvas.create_window(560, 55, anchor="nw", window=self.gametitle3, width=200, height=200)

    def game_start(self):
        print("Game Start ボタンがクリックされました")
        if self.controller:
            self.controller.show_frame("GamePanel1")
        
    def game_explanation(self):
        print("Gameの説明 ボタンがクリックされました")
        if self.controller:
            self.controller.show_frame("RulePanel")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Python版 TopPanel")
    root.geometry("750x500")
    
    # この例では、シンプルに TopPanel を作成して表示しています。
    # 複数のパネルを切り替える場合は、controller（例：フレーム管理用のクラス）を用意してください。
    panel = TopPanel(root)
    panel.pack(fill="both", expand=True)
    
    root.mainloop()
