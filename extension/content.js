
function getRentalPageData() {
  return {
    title: document.title,
    url: window.location.href,
    text: document.body.innerText.slice(0, 15000)
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "GET_RENTAL_PAGE") {
    sendResponse(getRentalPageData());
  }
});
