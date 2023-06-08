// window.addEventListener('load', (event) => {
//     var observer = new MutationObserver(function(mutations) {
//         var cardContainer = document.getElementById('card_container_all_others');
//         var codeViewer = document.getElementById('code_viewer');
//         var exportSteps = document.getElementById('export_steps');
//         if (cardContainer && codeViewer && exportSteps) {
//             var height = cardContainer.offsetHeight;
//             codeViewer.style.height = (0.8 * height) + 'px';
//             exportSteps.style.height = (0.2 * height) + 'px';
//             codeViewer.style.overflowY = "auto";
//         }
//     });

//     observer.observe(document.body, {
//         childList: true,
//         subtree: true
//     });
// });
