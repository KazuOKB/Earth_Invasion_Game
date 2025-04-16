import pygame
import sys

class LosePanel:
    def __init__(self, screen, mainframe):
        self.screen = screen
        self.mainframe = mainframe
        self.width, self.height = screen.get_size()

        # 大きな「Lose」文字用のフォント（サイズはお好みで調整）
        self.lose_font = pygame.font.SysFont(None, 150)
        self.lose_text = self.lose_font.render("L o s e...", True, (255, 60, 0))
        
        # タイトルに戻るボタン用のフォント（サイズはお好みで調整）
        self.button_font = pygame.font.SysFont(None, 48)
        self.button_text = self.button_font.render("Return to Title", True, (0, 0, 0))
        
        # ボタンの大きさと配置（画面中央下部付近に配置）
        btn_w, btn_h = 300, 50
        self.button_rect = pygame.Rect(
            (self.width - btn_w) // 2,
            self.height - btn_h - 40,
            btn_w, btn_h
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                # トップパネルへ戻す
                self.mainframe.panelChange("toppanel")

    def update(self, event):
        # 特に何もしない
        pass
    
    def draw_button(self, rect, text_surf):
        # ボタンの内部を白で塗りつぶすことで、背景画像の影響を受けずテキストが見えやすくなる
        pygame.draw.rect(self.screen, (255, 255, 255), rect)
        # ボタンの枠を描画（灰色、線幅4）
        pygame.draw.rect(self.screen, (140, 140, 140), rect, 4)
        # テキストをボタンの中央に配置するため、テキストの矩形を取得し中心位置に合わせる
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw(self):
        # 背景を黒で塗りつぶし
        self.screen.fill((0, 0, 0))

        # 「Lose」テキストを画面中央に描画
        lose_rect = self.lose_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(self.lose_text, lose_rect)

        # 戻るボタンの描画
        self.draw_button(self.button_rect, self.button_text)


# 挙動確認
if __name__ == "__main__":
    # ダミーのメインフレーム（Panel を呼び出すために必要）
    class DummyMainFrame:
        def panelChange(self, panel_name):
            print("Panel changed to:", panel_name)
    
    pygame.init()
    screen = pygame.display.set_mode((750, 500))
    pygame.display.set_caption("Panel")
    clock = pygame.time.Clock()
    
    # ダミーのメインフレームオブジェクトを作成し TopPanel に渡す
    dummy_mainframe = DummyMainFrame()
    panel = LosePanel(screen, dummy_mainframe)
    
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