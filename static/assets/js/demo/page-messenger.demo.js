var handleChatScrollBottom=function(){var e;(e=document.querySelector('.messenger-content-body [data-scrollbar="true"]')).scrollTop=e.scrollHeight-e.clientHeight,(e=document.querySelector(".messenger-content-body")).classList.remove("invisible")},handleMobileMessengerToggler=function(){$(document).on("click",'[data-toggle="messenger-content"]',(function(e){e.preventDefault(),$(".messenger").toggleClass("messenger-content-toggled")}))};$(document).ready((function(){handleChatScrollBottom(),handleMobileMessengerToggler()}));