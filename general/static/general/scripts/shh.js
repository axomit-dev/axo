function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

$( document ).ready(function() {
  $("#ayy").on('click', function() {
    var bases = ['ay', 'boi'];
    var base = bases[rand(0,1)];
    var c = base.slice(-1);
    var extendBy = rand(0,30);
    var extension = c.repeat(extendBy);
    var done = base + extension;
    console.log(done);
    var x = rand(5,95);
    var y = rand(5,95);

    var p = document.createElement("p");
    p.style.position = "fixed";
    p.style.left = x + '%';
    p.style.top = y + '%';
    p.innerHTML = done;

    $("#stuff").append(p);

    var count = $('#count').html();
    var newCount = parseInt(count) + 1;
    $('#count').html(newCount)
  });
});
