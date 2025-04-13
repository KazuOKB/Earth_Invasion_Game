import pygame
import sys

class TopPanel:
    def __init__(self, screen, mainframe):
        self.screen = screen
        self.mainframe = mainframe # メインフレームの参照を保持（panelChange() を呼び出せるようにする）
        
        # 画像の読み込み
        self.haikei = pygame.image.load("images/haikei.png")
        self.earth = pygame.image.load("images/earth2.png")
        self.ufo   = pygame.image.load("images/ufo004.png")
        
        # フォントの設定（タイトル・ボタン用）
        self.font_big   = pygame.font.SysFont("Serif", 200, bold=True)
        self.font_small = pygame.font.SysFont("Serif", 100, bold=True)
        self.font_btn   = pygame.font.SysFont("Arial", 20)
        
        # タイトル文字の作成
        self.title1 = self.font_small.render("Invade", True, (255, 60, 0))
        self.title2 = self.font_small.render("Earth!!", True, (255, 60, 0))
        #self.title3 = self.font_small.render("Earth!!", True, (255, 60, 0))
        
        # ボタンの矩形（位置(X,Y)とサイズ(X,Y)）
        self.btn1_rect = pygame.Rect(100, 340, 200, 40)  # Gameスタート
        self.btn3_rect = pygame.Rect(100, 420, 200, 40)  # Gameの説明
        
        # ボタンのテキスト作成（テキスト色は黒）
        self.btn1_text = self.font_btn.render("Game Start", True, (0, 0, 0))
        self.btn3_text = self.font_btn.render("Rule", True, (0, 0, 0))

    def handle_event(self, event):
        # マウスクリックがあったら、それがどのボタン内かを判定
        # event は pygame.event.get()によって得られる変数
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 現在のマウスの座標をタプルで返す
            pos = pygame.mouse.get_pos()
            # ボタンの領域にマウスの座標が含まれていればTrueを返す関数
            if self.btn1_rect.collidepoint(pos):
                print("Game start ボタンがクリックされました")
                # MainFrame の panelChange() を呼んで gamepanel1 に遷移
                self.mainframe.panelChange("gamepanel1")
            
            if self.btn3_rect.collidepoint(pos):
                print("Gameの説明 ボタンがクリックされました")
                # MainFrame の panelChange() を呼んで rulepanel に遷移
                self.mainframe.panelChange("rulepanel")  
    
    def update(self, event):
        # このパネルで特に更新処理がなければ pass
        pass

    def draw(self):
        # 背景画像を画面全体に描画
        # blit "bit block transfer"
        self.screen.blit(pygame.transform.scale(self.haikei, self.screen.get_size()), (0, 0))
        
        # その他の画像の描画
        self.screen.blit(self.earth, (530, 320))  # 地球画像 (右下)
        self.screen.blit(self.ufo, (20, 20))        # UFO画像 (左上)
        
        # タイトル文字の描画
        self.screen.blit(self.title1, (415, 35))
        self.screen.blit(self.title2, (415, 135))
        #self.screen.blit(self.title3, (415, 235))
        
        # ボタンの描画
        self.draw_button(self.btn1_rect, self.btn1_text)
        self.draw_button(self.btn3_rect, self.btn3_text)
    
    def draw_button(self, rect, text_surf):
        # ボタンの内部を白で塗りつぶすことで、背景画像の影響を受けずテキストが見えやすくなる
        pygame.draw.rect(self.screen, (255, 255, 255), rect)
        # ボタンの枠を描画（灰色、線幅4）
        pygame.draw.rect(self.screen, (140, 140, 140), rect, 4)
        # テキストをボタンの中央に配置するため、テキストの矩形を取得し中心位置に合わせる
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)



# 挙動確認
if __name__ == "__main__":
    # ダミーのメインフレーム（TopPanel を呼び出すために必要）
    class DummyMainFrame:
        def panelChange(self, panel_name):
            print("Panel changed to:", panel_name)
    
    pygame.init()
    screen = pygame.display.set_mode((750, 500))
    pygame.display.set_caption("TopPanel")
    clock = pygame.time.Clock()
    
    # ダミーのメインフレームオブジェクトを作成し TopPanel に渡す
    dummy_mainframe = DummyMainFrame()
    panel = TopPanel(screen, dummy_mainframe)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                panel.handle_event(event)
                panel.update(event)
        panel.draw()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()