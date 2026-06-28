import { z } from 'zod'

// Базовые правила
export const emailSchema = z
  .string()
  .min(1, 'Email обязателен')
  .email('Некорректный email')

export const passwordSchema = z
  .string()
  .min(1, 'Пароль обязателен')
  .min(8, 'Минимум 8 символов')
  .regex(/[A-Z]/, 'Нужна хотя бы одна заглавная буква')
  .regex(/[a-z]/, 'Нужна хотя бы одна строчная буква')
  .regex(/[0-9]/, 'Нужна хотя бы одна цифра')

export const usernameSchema = z
  .string()
  .min(3, 'Минимум 3 символа')
  .max(30, 'Максимум 30 символов')
  .regex(/^[a-zA-Z0-9_]+$/, 'Только буквы, цифры и _')
  .optional()
  .or(z.literal(''))

export const codeSchema = z
  .string()
  .min(1, 'Код обязателен')
  .length(6, 'Код должен содержать 6 цифр')
  .regex(/^\d+$/, 'Только цифры')

// Схемы форм
export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Пароль обязателен'),
})

export const registerSchema = z
  .object({
    email: emailSchema,
    username: usernameSchema,
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Подтвердите пароль'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

export const forgotPasswordSchema = z.object({
  email: emailSchema,
})

export const resetPasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string().min(1, 'Подтвердите пароль'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

export const twoFactorSchema = z.object({
  code: codeSchema,
})

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Текущий пароль обязателен'),
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, 'Подтвердите пароль'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

// Типы
export type LoginFormData = z.infer<typeof loginSchema>
export type RegisterFormData = z.infer<typeof registerSchema>
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>
export type TwoFactorFormData = z.infer<typeof twoFactorSchema>
export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>