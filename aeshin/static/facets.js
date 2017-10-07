$('#facets').change(function() {
  $('.bibitem').fadeOut('fast')
  var facets = $('#facets dd[id]').map(function() { return this.id })
  var selected = {}
  for (var f = 0; f < facets.length; f++) {
    selected[facets[f]] = $('#' + facets[f] + ' input[type=checkbox]:checked')
      .map(function() { return this.name })
      .get()
  }
  $('.bibitem').each(function() {
    var item = $(this)
    var show = Object.keys(selected)
      .map(function(facet) {
        return (selected[facet].indexOf(item.data(facet)) >= 0)
      })
      .every(function(x) { return x })
    if (show) $(this).delay(200).fadeIn('fast')
  })
})
