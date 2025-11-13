from rest_framework import serializers

from myapp.models import Product, Category
from django.contrib.auth.models import User


# from myapp.models import Product




class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    in_stock = serializers.BooleanField(default=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    image = serializers.ImageField(required=False, allow_null=True)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля.")
        return value

    def create(self, validated_data):
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.price = validated_data.get('price', instance.price)
        instance.in_stock = validated_data.get('in_stock', instance.in_stock)
        instance.category = validated_data.get('category', instance.category)


        image = validated_data.get('image')
        if image is not None:
            instance.image = image

        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id','username', 'email', 'password')

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user