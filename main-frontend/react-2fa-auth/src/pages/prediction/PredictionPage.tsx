import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { usePrediction } from '@/hooks/usePrediction';
import { Calculator, TrendingUp, Building2, MapPin, Home } from 'lucide-react';

// ===== Zod схема с кросс-валидацией =====
const CURRENT_YEAR = new Date().getFullYear();

const predictionSchema = z.object({
  // Площади
  total_meters: z.coerce.number().min(10, 'Минимум 10 м²').max(500, 'Максимум 500 м²'),
  living_meters: z.coerce.number().min(0, 'Не может быть отрицательной'),
  kitchen_meters: z.coerce.number().min(0, 'Не может быть отрицательной'),
  
  // Комнаты и этажи
  rooms_count: z.coerce.number().min(0, 'Минимум 0 (студия)').max(10, 'Максимум 10'),
  floor: z.coerce.number().min(1, 'Минимум 1 этаж'),
  floors_count: z.coerce.number().min(1, 'Минимум 1 этаж'),
  
  // Год постройки
  year_of_construction: z.coerce.number()
    .min(1850, 'Год не может быть раньше 1850')
    .max(CURRENT_YEAR, `Год не может быть позже ${CURRENT_YEAR}`),
  
  // Район и тип дома
  district: z.string().min(1, 'Выберите район'),
  house_type: z.string().min(1, 'Выберите тип дома'),
  renovation_category: z.string().min(1, 'Выберите тип ремонта'),
  
  // Горизонт прогноза
  horizon: z.enum(['now', '6_months', '1_year']),
}).refine(
  (data) => data.floor <= data.floors_count,
  {
    message: 'Этаж не может быть больше количества этажей в доме',
    path: ['floor'],
  }
).refine(
  (data) => data.living_meters <= data.total_meters,
  {
    message: 'Жилая площадь не может превышать общую',
    path: ['living_meters'],
  }
).refine(
  (data) => data.kitchen_meters <= data.total_meters,
  {
    message: 'Площадь кухни не может превышать общую',
    path: ['kitchen_meters'],
  }
).refine(
  (data) => (data.living_meters + data.kitchen_meters) <= data.total_meters,
  {
    message: 'Сумма жилой и кухни не может превышать общую площадь',
    path: ['kitchen_meters'],
  }
);

type FormValues = z.infer<typeof predictionSchema>;

const formatPrice = (v: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(v);

// Координаты центра Владивостока и моря
const VLADIVOSTOK_CENTER = { lat: 43.1155, lon: 131.8855 };
const SEA_POINT = { lat: 43.1000, lon: 131.9200 };

function calcDistanceKm(lat: number, lon: number, targetLat: number, targetLon: number): number {
  return Math.sqrt((lat - targetLat) ** 2 + (lon - targetLon) ** 2) * 111;
}

export function PredictionPage() {
  const { predict, result, isLoading } = usePrediction();
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(predictionSchema),
    defaultValues: {
      total_meters: 45,
      living_meters: 31.5,
      kitchen_meters: 6.75,
      rooms_count: 1,
      floor: 5,
      floors_count: 10,
      year_of_construction: 2010,
      district: '',
      house_type: '',
      renovation_category: '',
      horizon: 'now',
    },
  });

  const watchedValues = watch();

  const onSubmit = async (data: FormValues) => {
    // Вычисляем производные поля
    const building_age = CURRENT_YEAR - data.year_of_construction;
    const floor_ratio = data.floor / data.floors_count;
    const living_ratio = data.living_meters / data.total_meters;
    const kitchen_ratio = data.kitchen_meters / data.total_meters;

    // Гео-признаки (упрощённо — центр Владивостока)
    const dist_to_center_km = 5;
    const dist_to_sea_km = 5;

    // Формируем полный payload для бэкенда
    await predict({
      total_meters: data.total_meters,
      living_meters: data.living_meters,
      kitchen_meters: data.kitchen_meters,
      rooms_count: data.rooms_count,
      floor: data.floor,
      floors_count: data.floors_count,
      floor_ratio: Math.round(floor_ratio * 100) / 100,
      living_ratio: Math.round(living_ratio * 100) / 100,
      kitchen_ratio: Math.round(kitchen_ratio * 100) / 100,
      building_age,
      year_of_construction: data.year_of_construction,
      latitude: VLADIVOSTOK_CENTER.lat,
      longitude: VLADIVOSTOK_CENTER.lon,
      dist_to_center_km,
      dist_to_sea_km,
      infrastructure_count: 3,
      security_score: 2,
      has_intercom: 1,
      has_closed_territory: 0,
      has_code_door: 1,
      has_garage: 0,
      has_concierge: 0,
      offer_photos_count: 10,
      house_photos_count: 5,
      has_plan_photo: 1,
      // Передаём категориальные признаки как есть (бэкенд с extra="allow" примет)
      district: data.district,
      house_type: data.house_type,
      renovation_category: data.renovation_category,
    }, data.horizon);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Calculator className="h-6 w-6 text-blue-600" />
          Прогноз стоимости недвижимости
        </h1>
        <p className="text-gray-500 mt-1">
          Введите характеристики квартиры для расчёта рыночной стоимости
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Форма */}
        <Card>
          <CardHeader>
            <CardTitle>Характеристики квартиры</CardTitle>
            <CardDescription>Заполните параметры объекта</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              
              {/* Секция: Площади */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <Home className="h-4 w-4" /> Площади
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  <Input
                    label="Общая (м²)"
                    type="number"
                    step="0.1"
                    {...register('total_meters')}
                    error={errors.total_meters?.message}
                  />
                  <Input
                    label="Жилая (м²)"
                    type="number"
                    step="0.1"
                    {...register('living_meters')}
                    error={errors.living_meters?.message}
                  />
                  <Input
                    label="Кухня (м²)"
                    type="number"
                    step="0.1"
                    {...register('kitchen_meters')}
                    error={errors.kitchen_meters?.message}
                  />
                </div>
              </div>

              {/* Секция: Комнаты и этажи */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <Building2 className="h-4 w-4" /> Комнаты и этажи
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  <Input
                    label="Комнат"
                    type="number"
                    {...register('rooms_count')}
                    error={errors.rooms_count?.message}
                  />
                  <Input
                    label="Этаж"
                    type="number"
                    {...register('floor')}
                    error={errors.floor?.message}
                  />
                  <Input
                    label="Этажей в доме"
                    type="number"
                    {...register('floors_count')}
                    error={errors.floors_count?.message}
                  />
                </div>
              </div>

              {/* Секция: Здание */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <Building2 className="h-4 w-4" /> Здание
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Год постройки"
                    type="number"
                    {...register('year_of_construction')}
                    error={errors.year_of_construction?.message}
                  />
                  <Select
                    label="Тип дома"
                    options={[
                      { value: 'monolith', label: 'Монолитный' },
                      { value: 'brick', label: 'Кирпичный' },
                      { value: 'panel', label: 'Панельный' },
                      { value: 'block', label: 'Блочный' },
                      { value: 'other', label: 'Другой' },
                    ]}
                    {...register('house_type')}
                    error={errors.house_type?.message}
                  />
                </div>
              </div>

              {/* Секция: Расположение и ремонт */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <MapPin className="h-4 w-4" /> Расположение и ремонт
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <Select
                    label="Район"
                    options={[
                      { value: 'Ленинский', label: 'Ленинский' },
                      { value: 'Первомайский', label: 'Первомайский' },
                      { value: 'Советский', label: 'Советский' },
                      { value: 'Фрунзенский', label: 'Фрунзенский' },
                      { value: 'Первореченский', label: 'Первореченский' },
                    ]}
                    {...register('district')}
                    error={errors.district?.message}
                  />
                  <Select
                    label="Ремонт"
                    options={[
                      { value: 'premium', label: 'Премиум / Дизайнерский' },
                      { value: 'cosmetic', label: 'Косметический' },
                      { value: 'pre_finish', label: 'Предчистовая' },
                      { value: 'none', label: 'Без отделки' },
                    ]}
                    {...register('renovation_category')}
                    error={errors.renovation_category?.message}
                  />
                </div>
              </div>

              {/* Горизонт прогноза */}
              <Select
                label="Горизонт прогноза"
                options={[
                  { value: 'now', label: 'Текущая цена' },
                  { value: '6_months', label: 'Через 6 месяцев' },
                  { value: '1_year', label: 'Через 1 год' },
                ]}
                {...register('horizon')}
              />

              <Button type="submit" className="w-full" isLoading={isLoading}>
                Рассчитать
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Результат */}
        <div className="space-y-6">
          {result ? (
            <Card className="border-green-200 bg-green-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-800">
                  <TrendingUp className="h-5 w-5" />
                  Результат прогноза
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Прогнозируемая стоимость</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatPrice(result.predicted_price)}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-green-200">
                  <div>
                    <p className="text-xs text-gray-500">Цена за м²</p>
                    <p className="font-semibold">
                      {formatPrice(result.predicted_price_per_sqm)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Уверенность</p>
                    <Badge variant={result.confidence > 0.8 ? 'success' : 'warning'}>
                      {(result.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Модель: {result.model_version} •{' '}
                  {new Date(result.created_at).toLocaleString('ru-RU')}
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card className="flex flex-col items-center justify-center min-h-[300px] text-gray-400">
              <Calculator className="h-12 w-12 mb-4 opacity-30" />
              <p>Заполните форму и нажмите «Рассчитать»</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}