"""transfer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
# from rest_framework.documentation import include_docs_urls
# 同步
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^config/datasource/', include('environment.urls')),
    url(r'^task/pof/', include('datamoving.urls')),
    url(r'^dashboard/', include('datamoving.urls')),
    url(r'^config/rule/', include('ruleManage.urls')),
    url(r'^authority/', include('authority.urls')),
    url(r'^config/system', include('config.urls')),
   # url(r'^docs/', include_docs_urls(title='My API title')),

]
