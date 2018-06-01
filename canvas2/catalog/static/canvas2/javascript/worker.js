
self.addEventListener('message', function(e) {
    // var message = e.data + ' to myself!';
    setTimeout(
        self.postMessage(e.data),
        2000
    );
    self.close();
});

// function setFalse(){
//     this.isTyping = false;
//     Vue.set(this.vm.isTyping, i, false)
// }
