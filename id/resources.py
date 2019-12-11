from import_export import resources, widgets

from id.models import User, Country, Locality, Province, District


class LocalityWidget(widgets.CharWidget):
    def render(self, value, obj=None):
        return str(value).zfill(8)


class CountryResource(resources.ModelResource):
    class Meta:
        model = Country


class LocalityResource(resources.ModelResource):
    id = resources.Field(attribute="id", widget=LocalityWidget())
    class Meta:
        model = Locality
        exclude = ("state", "updated")


class ProvinceWidget(widgets.CharWidget):
    def render(self, value, obj=None):
        return str(value).zfill(2)


class ProvinceResource(resources.ModelResource):
    id = resources.Field(attribute="id", widget=ProvinceWidget())

    class Meta:
        model = Province


class DistrictWidget(widgets.CharWidget):
    def render(self, value, obj=None):
        return str(value).zfill(5)


class DistrictResource(resources.ModelResource):
    id = resources.Field(attribute="id", widget=DistrictWidget())

    class Meta:
        model = District
