# Compose the anime setting sheet (Windows PowerShell + System.Drawing)
Add-Type -AssemblyName System.Drawing
$d = Join-Path $PSScriptRoot "..\renders" | Resolve-Path
$fams = [System.Drawing.Text.InstalledFontCollection]::new().Families | ForEach-Object Name
$fn = @("Yu Gothic", "Meiryo", "MS Gothic") | Where-Object { $fams -contains $_ } | Select-Object -First 1

$W = 3600; $H = 6400
$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.InterpolationMode = 'HighQualityBicubic'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.Clear([System.Drawing.Color]::FromArgb(250, 246, 236))
$ink  = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(45, 35, 30))
$sub  = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(110, 98, 88))
$band = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(232, 222, 202))
$pen  = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(70, 58, 50)), 3
$fT = New-Object System.Drawing.Font $fn, 78, ([System.Drawing.FontStyle]::Bold)
$fS = New-Object System.Drawing.Font $fn, 34
$fC = New-Object System.Drawing.Font $fn, 30, ([System.Drawing.FontStyle]::Bold)
$fH = New-Object System.Drawing.Font $fn, 34, ([System.Drawing.FontStyle]::Bold)

function Panel($file, $x, $y, $w, $caption, [switch]$frame) {
    $im = [System.Drawing.Image]::FromFile("$d\$file")
    $h = [int]($im.Height * $w / $im.Width)
    $g.DrawImage($im, $x, $y, $w, $h)
    if ($frame) { $g.DrawRectangle($pen, $x, $y, $w, $h) }
    $g.DrawString($caption, $fC, $ink, $x + 4, $y + $h + 8)
    $im.Dispose()
    return $h
}
function Header($text, $y) {
    $g.FillRectangle($band, 20, $y, $W - 40, 56)
    $g.DrawString($text, $fH, $ink, 34, $y + 6)
}

# title
$g.DrawString("野比家", $fT, $ink, 30, 18)
$g.DrawString("NOBITA's HOUSE  ―  ゲーム空間設定資料 / Game Space Setting Sheet", $fS, $sub, 400, 62)

$y = 160
$h1 = Panel "anime_exterior.png"    20   $y 1770 "外観  EXTERIOR" -frame
$h2 = Panel "anime_cutaway_dollhouse.png" 1810 $y 1770 "全体断面  CUTAWAY (1F + 2F)" -frame
$y += [Math]::Max($h1, $h2) + 70

Header "立面図  ELEVATIONS" $y; $y += 76
$x = 20; $hh = 0
foreach ($p in @(@("elev_front.png", "正面図  FRONT"), @("elev_back.png", "背面図  BACK"),
                 @("elev_left.png", "側面図（左）  LEFT"), @("elev_right.png", "側面図（右）  RIGHT"))) {
    $hh = Panel $p[0] $x $y 875 $p[1]; $x += 895
}
$y += $hh + 70

Header "外構・パーツ  PARTS" $y; $y += 76
$x = 20
foreach ($p in @(@("vig_gate.png", "門扉・塀  GATE"), @("vig_genkan.png", "玄関  ENTRANCE"), @("vig_wall.png", "塀  BLOCK WALL"),
                 @("vig_bike.png", "駐輪場  BIKE SHELTER"), @("vig_iso.png", "全体アイソメ図  ISOMETRIC"))) {
    $hh = Panel $p[0] $x $y 700 $p[1]; $x += 715
}
$y += $hh + 70

$h1 = Panel "anime_cutaway_1F.png"  20   $y 1770 "1階平面  1F PLAN (CUTAWAY)" -frame
$h2 = Panel "anime_cutaway_2F.png"  1810 $y 1770 "2階平面  2F PLAN (CUTAWAY)" -frame
$y += [Math]::Max($h1, $h2) + 70

Header "のび太の部屋  NOBITA's ROOM" $y; $y += 76
$hr = Panel "anime_nobita_room.png" 20 $y 1770 "のび太の部屋  NOBITA's ROOM" -frame
$x0 = 1810; $yy = $y; $k = 0
foreach ($p in @(@("det_desk.png", "机まわり  DESK"), @("det_bookshelf.png", "本棚  BOOKSHELF"),
                 @("det_oshiire.png", "押入れ  OSHIIRE"), @("det_futon.png", "ベッド（布団）  BED"))) {
    $xx = $x0 + ($k % 2) * 895
    $hh = Panel $p[0] $xx $yy 875 $p[1] -frame
    if ($k % 2 -eq 1) { $yy += $hh + 60 }
    $k++
}
$y = [Math]::Max($y + $hr + 70, $yy + 10)
# crop to used height
$final = $bmp.Clone([System.Drawing.Rectangle]::new(0, 0, $W, [int][Math]::Min($H, $y)), $bmp.PixelFormat)
$out = "$d\NobitaHouse_AnimeSheet.png"
$final.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
"$fn  $W x $y -> $out"
