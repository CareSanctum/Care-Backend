from django.db import models
from user_onboarding.models import CustomUser
from django.utils.text import slugify
from django.utils.timezone import now
import random
import string
# Create your models here.

#global Variables to configure Percentage
B2B_COMMISSION_PERCENTAGE = 0
B2C_COMMISSION_PERCENTAGE = 0

def generate_referral_code(name):
    base_code = slugify(name)[:10].upper()
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{base_code}-{random_suffix}"


class B2BPartner(models.Model):
    registered_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="registered_b2b_partners")
    company_name = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if self.registered_by.role != "ADMIN":
            raise ValueError("Only Admins can register B2B Partners")
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            ReferralCode.objects.create(
                type="B2B_PARTNER",
                b2b_partner=self,
                code=generate_referral_code(self.company_name)
            )


    def __str__(self):
        return self.company_name
    
class B2CUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if self.user.role != "USERS":
            raise ValueError("B2C users can only be linked to  users")
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            ReferralCode.objects.create(
                type="B2C_USER",
                b2c_user=self,
                code=generate_referral_code(self.user.username)
            )

    
    def __str__(self):
        return self.user.username

class ReferralCode(models.Model):
    type = models.CharField(max_length=255, choices=(("B2B_PARTNER", "B2B Partner"), ("B2C_USER", "B2C user")))
    # only one of these fields will be filled depending on wether the referral code belongs to a b2b partner or a b2c user
    b2b_partner = models.OneToOneField(B2BPartner, on_delete=models.CASCADE, null=True, blank=True, related_name="referral_codes")
    b2c_user = models.OneToOneField(B2CUser, on_delete=models.CASCADE, null=True, blank=True, related_name="referral_code")
    code = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if self.b2b_partner and self.b2c_user:
            raise ValueError("A referral code cannot be linked to both a B2B Partner and a B2C User.")
        if not self.b2b_partner and not self.b2c_user:
            raise ValueError("A referral code must be linked to either a B2B Partner or a B2C User.")
        if self.type == "B2B_PARTNER" and not self.b2b_partner:
            raise ValueError("A B2B Partner referral code must be linked to a B2B Partner")
        elif self.type == "B2C_USER" and not self.b2c_user:
            raise ValueError("A B2C User referral code must be linked to a B2C User")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.type}"

class Lead(models.Model):
    user  = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    referred_through = models.ForeignKey(ReferralCode, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    date_referred = models.DateField(default=now)
    converted =models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - Referred through {self.referred_through.code}"

    

class Commission(models.Model):
    STATUS_CHOICES = (
        ("IN_PROCESS", "In Process"),
        ("PAID", "Paid"),
        ("NOT_PAID", "Not Paid"),
        ("REJECTED", "Rejected")
    )
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="IN_PROCESS")
    percentage = models.FloatField()
    amount = models.FloatField()
    date_converted = models.DateField(default=now)
    b2b_receipent = models.ForeignKey(B2BPartner, null=True, blank=True, on_delete=models.CASCADE)
    b2c_receipent = models.ForeignKey(B2CUser, null=True, blank=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.b2b_receipent and self.b2c_receipent:
            raise ValueError("A commission cannot be assigned to both a B2B Partner and a B2C User.")
        if not self.b2b_receipent and not self.b2c_receipent:
            raise ValueError("A commission must be assigned to either a B2B Partner or a B2C User.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.amount} - {self.status}"

    