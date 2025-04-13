import pygame
import sys

class RulePanel:
    def __init__(self, screen, mainframe):
        self.screen = screen
        self.mainframe = mainframe  # 画面遷移用にメインフレームの参照を保持
        self.font = pygame.font.SysFont("Arial", 36)

        # 背景画像の読み込み
        self.rule_img = pygame.image.load("images/rule.png").convert()
        # ボタンの矩形を Java の setBounds(60,380,200,50) に合わせて設定
        self.btn_rect = pygame.Rect(60, 400, 200, 50)
        self.btn_text = "Return Top"
        self.font_btn = pygame.font.SysFont("Arial", 20)
        # Java の LineBorder(Color.RED, 4, true) に相当する設定
        self.border_color = (150, 150, 150)
        self.border_width = 4

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if self.btn_rect.collidepoint(pos):
                print("Return Top ボタンがクリックされました")
                self.mainframe.panelChange("toppanel")

    def update(self, event):
        # 今回は特に更新処理は必要なければ pass でOK
        pass

    def draw(self):
        # 画面サイズ取得
        width, height = self.screen.get_size()
        # まず背景を黒で塗りつぶす
        self.screen.fill((0, 0, 0))
        # 背景画像を画面全体にスケーリングして描画
        bg_scaled = pygame.transform.scale(self.rule_img, (width, height))
        self.screen.blit(bg_scaled, (0, 0))
        # ボタンを描画
        # 内部は薄い灰色で塗りつぶす
        button_fill_color = (200, 200, 200)
        pygame.draw.rect(self.screen, button_fill_color, self.btn_rect)
        # 赤いボーダーを描画
        pygame.draw.rect(self.screen, self.border_color, self.btn_rect, self.border_width)
        # ボタンテキストを中央に配置して描画
        btn_text_surf = self.font_btn.render(self.btn_text, True, (0, 0, 0))
        text_rect = btn_text_surf.get_rect(center=self.btn_rect.center)
        self.screen.blit(btn_text_surf, text_rect)



# 挙動確認
if __name__ == "__main__":
    # ダミーのメインフレーム（TopPanel を呼び出すために必要）
    class DummyMainFrame:
        def panelChange(self, panel_name):
            print("Panel changed to:", panel_name)
    
    pygame.init()
    screen = pygame.display.set_mode((750, 500))
    pygame.display.set_caption("RulePanel")
    clock = pygame.time.Clock()
    
    # ダミーのメインフレームオブジェクトを作成し、確認したい Panel に渡す
    dummy_mainframe = DummyMainFrame()
    panel = RulePanel(screen, dummy_mainframe)
    
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