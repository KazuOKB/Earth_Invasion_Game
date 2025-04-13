import pygame
import sys

# カスタムタイマーイベント
TIMER_EVENT = pygame.USEREVENT + 1

class JavaTeamGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((750, 500))
        pygame.display.set_caption("Java Shooting Game")
        self.clock = pygame.time.Clock()
        
        # 自機の画像読み込みとスケーリング（ufo003.png を 50×38 にする）
        self.jiki_img_original = pygame.image.load("images/ufo003.png").convert_alpha()
        self.jiki_img = pygame.transform.scale(self.jiki_img_original, (50, 38))
        self.jiki_y = 10   # 自機の初期 y 座標
        self.jiki_x = 10   # 自機は常に x=10 に描画
        
        # 自機のビームの初期設定
        self.jiki_beam_x = 30
        self.jiki_beam_y = 30
        self.jiki_beam_flg = 0  # 0: ビーム未発射、1: ビーム発射中
        
        # 80ミリ秒ごとにタイマーイベントを発生させる
        pygame.time.set_timer(TIMER_EVENT, 80)
    
    def handle_key(self, event):
        if event.type == pygame.KEYDOWN:
            # 上矢印キー：自機を上へ移動（y 座標が 0 より大きければ）
            if event.key == pygame.K_UP and self.jiki_y > 0:
                self.jiki_y -= 10
            # 下矢印キー：自機を下へ移動（y 座標が 430 以下なら）
            elif event.key == pygame.K_DOWN and self.jiki_y < 430:
                self.jiki_y += 10
            # Z キーでビーム発射（未発射状態の場合）
            elif event.key == pygame.K_z and self.jiki_beam_flg == 0:
                self.jiki_beam_x = 40
                self.jiki_beam_y = self.jiki_y + 15
                self.jiki_beam_flg = 1
    
    def update(self, event):
        # タイマーイベントでビームの座標を更新
        if event.type == TIMER_EVENT:
            if self.jiki_beam_flg == 1:
                self.jiki_beam_x += 200
            # ビームが画面外（ウィンドウ幅を超えたら）になったら発射フラグをリセット
            if self.jiki_beam_x > self.screen.get_width():
                self.jiki_beam_flg = 0
    
    def draw(self):
        # 背景を黒で塗りつぶす
        self.screen.fill((0, 0, 0))
        # 自機の描画（常に x=10, y=jiki_y の位置に 50×38 サイズ）
        self.screen.blit(self.jiki_img, (10, self.jiki_y))
        # ビームが発射中なら、黄色の線を描画（始点 (50, jiki_beam_y) から終点 (jiki_beam_x+100, jiki_beam_y)）
        if self.jiki_beam_flg == 1:
            pygame.draw.line(self.screen, (255, 255, 0), (50, self.jiki_beam_y), (self.jiki_beam_x + 100, self.jiki_beam_y), 3)
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                # ウィンドウを閉じると running を False にして終了
                if event.type == pygame.QUIT:
                    running = False
                # キーボード入力の処理
                self.handle_key(event)
                # タイマーイベントでビーム更新
                self.update(event)
            # 描画処理
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = JavaTeamGame()
    game.run()
