<p>${etappe.start_timestamp.strftime('%B %y')} to ${etappe.end_timestamp.strftime('%B %y')}</p>

<div class="galleryimages">
    % for image in etappe.images:
    <div class="thumbIndv">
      <img src="static${image.location}${image.name}"/>
    </div>
    % endfor
</div>

