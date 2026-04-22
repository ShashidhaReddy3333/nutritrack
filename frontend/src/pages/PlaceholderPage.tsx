import Layout from '../components/Layout';

interface Props {
  title: string;
  phase: number;
  description: string;
}

export default function PlaceholderPage({ title, phase, description }: Props) {
  return (
    <Layout>
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center text-2xl mb-4">🚧</div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        <p className="text-gray-500 mt-2 max-w-md">{description}</p>
        <div className="mt-4 bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
          Coming in Phase {phase}
        </div>
      </div>
    </Layout>
  );
}
