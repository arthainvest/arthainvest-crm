import { LOAN_PRODUCTS } from './loanProducts';

describe('LOAN_PRODUCTS', () => {
  test('every product has a unique id', () => {
    const ids = LOAN_PRODUCTS.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('every product has the fields the UI relies on', () => {
    LOAN_PRODUCTS.forEach((p) => {
      expect(p.id).toEqual(expect.any(String));
      expect(p.name).toEqual(expect.any(String));
      expect(p.icon).toEqual(expect.any(String));
    });
  });

  test('includes the loan types the backend accepts (LAP/OD/CC/Home/Business/Project)', () => {
    const ids = LOAN_PRODUCTS.map((p) => p.id);
    expect(ids).toEqual(['LAP', 'OD', 'CC', 'Home', 'Business', 'Project']);
  });
});
