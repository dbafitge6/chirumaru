export type Store = {
  id: string;
  name: string;
  address: string;
  phone: string;
  hours: string;
  photoUrl: string;
  photoUrls: string[];
  tags: string[];
  area: string;
  website: string;
  mapUrl: string;
  memo: string;
  menu: string;
  updatedAt: string;
};

export type StoreFilters = {
  keyword: string;
  area: string;
  tags: string[];
};
