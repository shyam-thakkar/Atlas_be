
class TechRegistry(models.Model):
    ICON_TYPE_CHOICES = [
        ('svg', 'SVG'),
        ('png', 'PNG'),
        ('url', 'URL'),
        ('iconify', 'Iconify'),
    ]
    COLOR_VARIANT_CHOICES = [
        ('colored', 'Colored'),
        ('black', 'Black'),
        ('white', 'White'),
    ]

    display_name = models.CharField(max_length=100)
    code_name = models.CharField(max_length=100, unique=True, help_text="Used in bio like {{code_name}}")
    icon_type = models.CharField(max_length=20, choices=ICON_TYPE_CHOICES, default='url')
    icon_path = models.FileField(upload_to='tech_icons/', blank=True, null=True, help_text="Stored file path for SVG/PNG")
    icon_source_url = models.URLField(blank=True, null=True, help_text="Where icon was fetched from")
    doc_url = models.URLField(blank=True, null=True)
    color_variant = models.CharField(max_length=20, choices=COLOR_VARIANT_CHOICES, default='colored')
    
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.code_name = self.code_name.lower().replace(' ', '-')
        super().save(*args, **kwargs)
