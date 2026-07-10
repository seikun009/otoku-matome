// ============================================================
// 楽天API（ブラウザ側で取得）— 任意
// 使わない場合はこのファイルの中身を空のままにしておけばOK。
//
// 使うとき:
//  1) https://webservice.rakuten.co.jp/ で「New App」を Web application として登録
//  2) Application URL / Allowed domains に自分の GitHub Pages ドメインを設定
//     例: https://<ユーザー名>.github.io
//  3) 発行された applicationId と accessKey を下に貼る
//  ※ Allowed domains 制限があるため、他ドメインからは弾かれる（キー直書きでも実害は限定的）
// ============================================================

const RAKUTEN = {
  applicationId: "",   // ← ここに貼る
  accessKey: "",       // ← ここに貼る（2026年仕様で必須）
  keyword: "ポイント還元 期間限定",
  hits: 6,
};

(async function () {
  if (!RAKUTEN.applicationId || !RAKUTEN.accessKey) return; // 未設定なら何もしない

  const base = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401";
  const params = new URLSearchParams({
    applicationId: RAKUTEN.applicationId,
    accessKey: RAKUTEN.accessKey,
    format: "json",
    formatVersion: "2",
    keyword: RAKUTEN.keyword,
    hits: String(RAKUTEN.hits),
    sort: "-updateTimestamp",
  });

  try {
    const res = await fetch(`${base}?${params}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    const items = data.Items || [];
    if (!items.length) return;

    const html = items.map((it) => `
      <a class="row" href="${it.itemUrl}" target="_blank" rel="noopener">
        <p class="t">${it.itemName}</p>
        <p class="m">
          <span class="src">楽天 ¥${Number(it.itemPrice).toLocaleString()}</span>
          <time>ポイント${it.pointRate || 1}倍</time>
        </p>
      </a>`).join("");

    const sec = document.getElementById("rakuten");
    sec.innerHTML =
      `<header class="sec"><span class="stamp stamp-ink">楽天</span>` +
      `<span class="cnt">${items.length}件</span></header>` +
      `<div class="list">${html}</div>`;
    sec.hidden = false;
  } catch (e) {
    console.warn("楽天API取得失敗:", e);
  }
})();
