#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ Magick Counter : mgcount.cgi - 2011/05/14
#│ Copyright (c) KentWeb
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use Image::Magick;

# 設定データ認識
require "./init.cgi";
my %cf = &init;

# 時間取得
my $time = time;

# 二重アクセスチェック
my $is_duplicate_count;
if ($cf{limit_time} > 0) {

	# クッキー取得
	my $cook_time = &get_cookie;

	# 二重アクセスチェック
	if ($cook_time && $cook_time > $time) {
		$is_duplicate_count = 1;
	}
}

# カウント判定
my $can_count_up = can_count_up($is_duplicate_count, $cf{ignore_bot});

# データ読込
open(DAT,"+< $cf{datfile}");
eval "flock(DAT, 2);";
my $data = <DAT>;

# カウントアップしてよい条件を満たす場合にインクリメント
if ($can_count_up) {
	seek(DAT, 0, 0);
	print DAT ++$data;
	truncate(DAT, tell(DAT));
}
close(DAT);

# クッキー格納
&set_cookie if ($can_count_up && $cf{limit_time} > 0);

# 桁数調整
while ( length($data) < $cf{digit} ) {
	$data = '0' . $data;
}

# Magick起動
my $img = Image::Magick -> new;

# 画像読込
foreach ( split(//, $data) ) {
	$img -> Read("$cf{gifdir}/$_.gif");
}

# 画像連結
$img = $img -> Append(stack => 'false');

# 画像表示
print "Content-type: image/gif\n\n";
binmode(STDOUT);
$img -> Write('gif:-');
exit;

#-------------------------------------------------
#  クッキー発行
#-------------------------------------------------
sub set_cookie {
	# 有効時間定義
	my $gtime = $time += $cf{limit_time} * 60;

	# 国際標準時取得
	my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = gmtime($gtime);
	my @mon  = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;
	my @week = qw|Sun Mon Tue Wed Thu Fri Sat|;

	# 有効期限をフォーマット
	my $gmt = sprintf("%s, %02d-%s-%04d %02d:%02d:%02d GMT",
						$week[$wday], $mday, $mon[$mon], $year + 1900, $hour, $min, $sec);

	# クッキー発行
	print "Set-Cookie: mgcounter=$time; expires=$gmt\n";
}

#-------------------------------------------------
#  クッキー取得
#-------------------------------------------------
sub get_cookie {
	# クッキーを取得
	my $cook = $ENV{HTTP_COOKIE};

	# クッキーデータ抽出
	my $cook_data;
	foreach ( split(/;/, $cook) ) {
		my ($key, $val) = split(/=/);
		$key =~ s/\s//g;

		if ($key eq 'mgcounter') {
			$cook_data = $val;
			last;
		}
	}
	return $cook_data;
}

sub can_count_up {
	my $is_duplicate_count = shift;
	my $is_ignore_bot = shift;

	if ($is_ignore_bot) {
		# 重複カウント判定＋BOT判定
		return !$is_duplicate_count && is_human();
	} else {
		# 重複カウント判定のみ
		return !$is_duplicate_count;
	}
}

sub is_human {
	my $is_bot_ua = is_bot_ua($ENV{HTTP_USER_AGENT});
	my $is_jp_host = is_jp_host(get_remote_host());
	my $is_ipv6 = is_ipv6($ENV{REMOTE_ADDR});

	# BOTUAならBOT確定、JPなら人間扱い、IPv6は国判定が重いので人間扱い
	my $is_human = !$is_bot_ua && ($is_jp_host || $is_ipv6);
	return $is_human;
}

sub is_bot_ua {
	my $user_agent = shift;
	return $user_agent =~ /bot|curl|wget|google|bing|mastodon|misskey|pleroma|akkoma|lemmy|activitypub|hatena|github|tumblr|meta|\+http|go|python|client|node|undici/;
}

sub get_remote_host {
	if (defined $ENV{REMOTE_HOST}) {
		return $ENV{REMOTE_HOST};
	} else {
		my $ip_addr = $ENV{REMOTE_ADDR};
		my $bin = pack('C4', split(/\./, $ip_addr));
		my ($host_name) = gethostbyaddr($bin, 2);
		return $host_name;
	}
}

sub is_jp_host {
	my $remote_host = shift;
	return $remote_host =~ /\.(jp|nifty\.com|2iij\.net|bbtec\.net)$/;
}

sub is_ipv6 {
	my $ip_addr = shift;
	return $ip_addr =~ /:/;
}
