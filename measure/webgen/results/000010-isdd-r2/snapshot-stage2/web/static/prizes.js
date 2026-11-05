/* Prize List 画面: 景品の一覧を描く。 */
(function () {
  "use strict";

  var app = window.WheelApp;
  var count = document.getElementById("prize-count");
  var list = document.getElementById("prize-list");
  var error = document.getElementById("prize-error");

  app.getJSON("/api/prizes").then(function (data) {
    var prizes = data.prizes;
    count.textContent = prizes.length + (prizes.length === 1 ? " prize" : " prizes") + " to win on the wheel";
    prizes.forEach(function (prize) {
      var item = document.createElement("li");
      item.className = "card";

      var title = document.createElement("h2");
      title.textContent = prize.name;

      var description = document.createElement("p");
      description.textContent = prize.description || "";

      item.appendChild(title);
      item.appendChild(description);
      list.appendChild(item);
    });
  }).catch(function () {
    app.showError(error, "The prize list could not be loaded.");
  });
})();
