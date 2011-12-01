
$(document).ready(function()
  {

   // Fer els numeros dels entorns clicables que mostrin el seu
   $('.entornlink').click(function() 
     {
      entorn = $(this).text()
      $('.info').hide()      
      $('#entorn-'+entorn).show()
      
     });
     
     
    $('#instancesearch').keyup(function()
       {
       value = $(this).attr('value')
       if (value=='')
        $('#instancies .instancia').show()
       else
        { 
           $('#instancies .instancia').hide()          
           $('#instancies .instancia:contains('+value+')').show()    
           $('#globalinstancecount').text('('+$('#instancies .instancia:contains('+value+')').length+')')
         }    
       });  
       
    $('.more').click(function()
        {
        $(this).parent().find('.details').toggle()
        });   

    $('#globalinstancecount').text('('+$('#instancies .instancia').length+')')


});

function showentorns()
{
      $('#instancies').hide()      
      $('#entorns').show()
}

function showinstancies()
{
      $('#entorns').hide()
      $('#instancies').show()   
}

function purgeVarnish(port)
{
    $.get('purge',{telnetport:port},function(data){
      if (data['result']==true)
        {
          alert("S'ha purgat el varnish de sylar.upc.es.")
        }
      else
        {
          alert("No s'ha pogut purgat el varnish de al port.")          
        }
    },'json')
    
}
