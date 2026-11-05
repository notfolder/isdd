/* 全画面で使う共通の処理: 名前の保存、JSON の取得、エラー表示。 */
(function () {
  "use strict";

  var NAME_KEY = "wheelOfFortune.playerName";

  function parseResponse(response) {
    return response.json().catch(function () { return {}; }).then(function (data) {
      if (!response.ok) {
        throw new Error((data && data.error) || "The request failed. Please try again.");
      }
      return data;
    });
  }

  window.WheelApp = {
    loadName: function () {
      try {
        return window.localStorage.getItem(NAME_KEY) || "";
      } catch (error) {
        return "";
      }
    },
    saveName: function (name) {
      try {
        window.localStorage.setItem(NAME_KEY, name);
      } catch (error) {
        /* 保存できなくても画面の操作は続ける */
      }
    },
    getJSON: function (url) {
      return fetch(url, { headers: { Accept: "application/json" } }).then(parseResponse);
    },
    postJSON: function (url, body) {
      return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body)
      }).then(parseResponse);
    },
    showError: function (element, message) {
      element.textContent = message || "";
    },
    /* 当選日時（UTC の ISO 8601）を、利用者のブラウザの地域形式（英語表記）の日付と時刻にする。 */
    formatWonAt: function (text) {
      var date = new Date(text);
      if (isNaN(date.getTime())) {
        return text;
      }
      return date.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });
    }
  };
})();
